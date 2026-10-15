#!/usr/bin/env python3
"""Publish early CI evidence without rebasing/mutating the checkout still under test.
Only the session branch is updated. A temporary Git index overlays the requested
report files on the latest remote tree; HEAD and the real index remain untouched.
"""
import os
from pathlib import Path
import subprocess
import sys
import tempfile

BRANCH = 'arena/10158ad9-aimods'


def publish(paths, repo='.'):
    repo = Path(repo).resolve()
    files = []
    for name in paths:
        path = (repo/name).resolve()
        relative = path.relative_to(repo)
        if relative.parts[0] != 'reports' or not path.is_file():
            raise ValueError('Only existing report files may be published: '+str(name))
        files.append(str(relative))
    if not files:
        raise ValueError('No evidence files')

    def git(*args, env=None):
        return subprocess.check_output(['git', *args], cwd=repo, env=env, text=True).strip()

    with tempfile.TemporaryDirectory(prefix='evidence-index-') as temp:
        env = dict(os.environ, GIT_INDEX_FILE=str(Path(temp)/'index'))
        for attempt in range(3):
            git('fetch', 'origin', BRANCH)
            parent = git('rev-parse', 'FETCH_HEAD')
            git('read-tree', parent, env=env)
            git('add', '--', *files, env=env)
            tree = git('write-tree', env=env)
            if tree == git('rev-parse', parent+'^{tree}'):
                return parent
            commit = git('commit-tree', tree, '-p', parent, '-m',
                         '[gametest-evidence] Early required-test diagnostics', env=env)
            pushed = subprocess.run(['git', 'push', 'origin', commit+':'+BRANCH], cwd=repo)
            if pushed.returncode == 0:
                return commit
        raise RuntimeError('Evidence push rejected three times; no force push attempted')


if __name__ == '__main__':
    print(publish(sys.argv[1:]))
