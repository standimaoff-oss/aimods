#!/usr/bin/env python3
"""Capture authentic Minecraft F2 previews of the WWI Mark I and Gewehr 98."""
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import verify_game as game  # noqa: E402


def run():
    game.configure("server", server=True)
    client_dir = game.RUNS / "client"
    client_dir.mkdir(parents=True, exist_ok=True)
    (client_dir / "options.txt").write_text("""version:3465
lang:en_us
tutorialStep:none
onboardAccessibility:false
skipMultiplayerWarning:true
joinedFirstServer:true
renderDistance:6
simulationDistance:5
maxFps:30
guiScale:2
fov:0.0
graphicsMode:0
renderClouds:\"false\"
pauseOnLostFocus:false
narrator:0
soundCategory_master:0.0
chatVisibility:0
chatOpacity:0.0
fullscreen:false
overrideWidth:1280
overrideHeight:800
""")

    server, server_log = game.launch("server", game.gradle("runServer"))
    game.wait_log(server, server_log, "Done (")
    client, client_log = game.launch(
        "client", game.gradle("runClient", "-PautoJoin=127.0.0.1:25565")
    )
    game.wait_log(server, server_log, "TestPlayer joined the game", 900)
    game.wait_log(client, client_log, "Loaded", 180)
    time.sleep(12)

    window = subprocess_window()
    game.key("windowfocus", "--sync", window)
    for cmd in [
        "time set 6000",
        "gamerule doDaylightCycle false",
        "weather clear",
        "gamerule doWeatherCycle false",
        "gamerule doMobSpawning false",
        "gamemode creative TestPlayer",
        "fill -32 -61 -32 32 -61 40 minecraft:grass_block",
        "summon aiarsenal:mark_i 0 -60 16 {PersistenceRequired:1b}",
        "tp TestPlayer -10 -59 1 -35 4",
        "clear TestPlayer",
    ]:
        game.command(cmd)
    spawned = game.command(
        "execute if entity @e[type=aiarsenal:mark_i,limit=1] run say PREVIEW_MARK_I_SPAWNED"
    )
    if "PREVIEW_MARK_I_SPAWNED" not in spawned:
        raise AssertionError(f"Mark I did not spawn: {spawned}")
    time.sleep(5)
    game.key("key", "F1")  # remove HUD for a clean, unaltered in-game view
    time.sleep(2)
    game.screenshot("mark-i-exterior")
    game.key("key", "F1")

    for cmd in [
        "clear TestPlayer",
        "item replace entity TestPlayer hotbar.0 with aiarsenal:gewehr98{Ammo:5}",
        "tp TestPlayer 0 -60 0 0 0",
    ]:
        game.command(cmd)
    game.key("key", "1")
    time.sleep(4)
    game.key("key", "F1")
    time.sleep(1)
    game.screenshot("gewehr98-first-person")
    game.key("mousedown", "3")
    time.sleep(2)
    game.screenshot("gewehr98-aim")
    game.key("mouseup", "3")
    game.key("key", "F1")
    time.sleep(1)

    if client.poll() is not None or server.poll() is not None:
        raise RuntimeError("Minecraft exited during preview capture")


def subprocess_window():
    import subprocess
    windows = subprocess.check_output(
        ["xdotool", "search", "--name", "Minecraft"], text=True
    ).splitlines()
    if not windows:
        raise RuntimeError("Minecraft window not found")
    return windows[-1]


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        message = str(exc).replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
        print(f"::error title=Preview capture::{message}", flush=True)
        for path in sorted(game.LOGS.glob("*.log")):
            lines = path.read_text(errors="replace").splitlines()[-25:]
            if not lines:
                continue
            tail = "\n".join(lines)
            print(f"::group::Preview diagnostics: {path.name}", flush=True)
            print(tail, flush=True)
            print("::endgroup::", flush=True)
            safe_tail = tail[-3500:].replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
            print(f"::error title={path.name} diagnostic tail::{safe_tail}", flush=True)
        raise
    finally:
        game.cleanup()
