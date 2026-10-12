"""Build only committed source and record the exact source and wheel identities."""
import argparse
import ast
import hashlib
import importlib.metadata as metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args], text=True).strip()


def assignment(source, name):
    for node in ast.parse(source).body:
        if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == name for target in node.targets):
            return ast.literal_eval(node.value)
    raise RuntimeError('Missing assignment: ' + name)


def build(output):
    if git('status', '--porcelain', '--untracked-files=all'):
        raise RuntimeError('Commit or isolate local changes before building a release')
    manifest = json.loads((ROOT / 'fork/manifest.json').read_text())
    subprocess.run(['git', '-C', str(ROOT), 'merge-base', '--is-ancestor',
                    manifest['upstream_commit'], 'HEAD'], check=True)
    commit = git('rev-parse', 'HEAD')
    epoch = git('show', '-s', '--format=%ct', 'HEAD')
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='telethon-fork-') as temp:
        temp = Path(temp)
        source = temp / 'source'
        source.mkdir()
        archive = temp / 'source.tar'
        subprocess.run(['git', '-C', str(ROOT), 'archive', '--format=tar',
                        '--output=' + str(archive), commit], check=True)
        with tarfile.open(archive) as tar:
            tar.extractall(source, filter='data')
        env = dict(os.environ, SOURCE_DATE_EPOCH=epoch, PYTHONHASHSEED='0')
        subprocess.run([sys.executable, '-m', 'pip', 'wheel', '--no-deps',
                        '--no-build-isolation', '--wheel-dir', str(temp / 'wheels'), str(source)],
                       env=env, check=True)
        wheel, = (temp / 'wheels').glob('*.whl')
        with zipfile.ZipFile(wheel) as package:
            version = assignment(package.read('telethon/version.py'), '__version__')
            layer = assignment(package.read('telethon/tl/alltlobjects.py'), 'LAYER')
        if version != manifest['version'] or layer != manifest['layer']:
            raise RuntimeError('Built version or TL layer differs from fork manifest')
        destination = output / wheel.name
        receipt_path = output / (wheel.name + '.json')
        if destination.exists() or receipt_path.exists():
            raise RuntimeError('Release already exists; choose a new output directory or version')
        receipt = {
            'source_commit': commit,
            'upstream_commit': manifest['upstream_commit'],
            'source_tar_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
            'wheel': wheel.name,
            'wheel_sha256': hashlib.sha256(wheel.read_bytes()).hexdigest(),
            'version': version,
            'layer': layer,
            'opentele_version': manifest['opentele_version'],
            'python': sys.version,
            'source_date_epoch': epoch,
            'builder': {name: metadata.version(name) for name in ('pip', 'hatchling')},
        }
        shutil.copyfile(wheel, destination)
        receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
        print('Wheel:', destination)
        print('Receipt:', receipt_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'dist/fork')
    build(parser.parse_args().output)
