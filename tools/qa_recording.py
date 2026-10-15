"""Real X11-window + PulseAudio monitor capture; never a rendered/mock gameplay video."""
import json
import os
from pathlib import Path
import signal
import subprocess
import time


class Recording:
    def __init__(self, game, name):
        self.game = game
        self.name = name
        self.process = None
        if os.environ.get('QA_RECORD') != '1':
            return
        folder = game.OUT / 'videos'
        folder.mkdir(parents=True, exist_ok=True)
        self.path = folder / (name + '.mp4')
        self.log = (game.LOGS / ('record-' + name + '.log')).open('w')
        window = subprocess.check_output(['xdotool', 'search', '--name', 'Minecraft'], text=True).splitlines()[-1]
        self.process = subprocess.Popen(['ffmpeg', '-nostdin', '-y', '-hide_banner',
            '-thread_queue_size', '1024', '-f', 'x11grab', '-framerate', '20',
            '-window_id', window, '-i', os.environ.get('DISPLAY', ':99'),
            '-thread_queue_size', '1024', '-f', 'pulse', '-fragment_size', '4096',
            '-sample_rate', '48000', '-i', 'qa.monitor',
            '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '24', '-pix_fmt', 'yuv420p',
            '-threads', '1', '-vsync', '0', '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', str(self.path)],
            stdout=self.log, stderr=subprocess.STDOUT, start_new_session=True)
        game.PROCESSES.append(self.process)
        self.start = time.monotonic()
        self.reload_at = None
        time.sleep(.7)
        if self.process.poll() is not None:
            raise RuntimeError('recording failed: ' + name)

    def reload(self):
        if self.process:
            self.reload_at = time.monotonic() - self.start

    def stop(self):
        if not self.process:
            return
        os.killpg(self.process.pid, signal.SIGINT)
        code = self.process.wait(timeout=30)
        self.log.close()
        assert code in (0, 255), (self.name, code)
        probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams',
            '-show_format', '-of', 'json', str(self.path)], text=True))
        assert {'audio', 'video'} <= {s['codec_type'] for s in probe['streams']}
        assert float(probe['format']['duration']) > 5
        # Decode the ACTUAL game recording to verify audible, non-clipped output, not just an OGG resource.
        import numpy as np
        audio = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(self.path),
            '-vn', '-ac', '1', '-ar', '22050', '-f', 'f32le', '-'])
        samples = np.frombuffer(audio, dtype='<f4')
        rms = float(np.sqrt(np.mean(samples * samples)))
        peak = float(np.max(np.abs(samples)))
        assert rms > .0001 and peak > .002, f'{self.name}: silent gameplay capture'
        assert peak < .99, f'{self.name}: gameplay audio peak exceeds headroom: {peak}'
        report = {'video': self.path.name, 'duration': float(probe['format']['duration']),
                  'reload_seconds': self.reload_at, 'audio_rms': rms, 'audio_peak': peak,
                  'capture': 'X11 Minecraft window + PulseAudio qa.monitor; continuous, not frame synthesis'}
        (self.game.LOGS / ('video-' + self.name + '.json')).write_text(json.dumps(report, indent=2) + '\n')
        if self.reload_at is not None:
            # Separate source frames for agent inspection. NOT labelled F2 screenshots.
            frames = self.game.OUT / 'video-review' / self.name
            frames.mkdir(parents=True, exist_ok=True)
            for i, offset in enumerate((.15, .6, 1.1, 1.7, 2.3, 3.2)):
                subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(self.reload_at + offset),
                    '-i', str(self.path), '-frames:v', '1', str(frames / f'{i+1:02}.png')], check=True)
        print('CONTINUOUS VIDEO/AUDIO PASS', report, flush=True)
