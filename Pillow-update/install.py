from __future__ import print_function
import platform
import subprocess
import sys

packages = {
    'win32-3.5': 'Pillow-6.1.0.dev0-cp35-cp35m-win32.whl',
    'win32-3.6': 'Pillow-6.1.0.dev0-cp36-cp36m-win32.whl',
    'win32-3.7': 'Pillow-6.1.0.dev0-cp37-cp37m-win32.whl',
    'win64-3.5': 'Pillow-6.1.0.dev0-cp35-cp35m-win_amd64.whl',
    'win64-3.6': 'Pillow-6.1.0.dev0-cp36-cp36m-win_amd64.whl',
    'win64-3.7': 'Pillow-6.1.0.dev0-cp37-cp37m-win_amd64.whl',
}


if __name__ == '__main__':
    print('This script will update your Pillow version to fix Unicode rendering on Windows')
    print('Checking system...')
    print()

    if sys.platform != 'win32':
        print('A Pillow update is only necessary on Windows!')
        sys.exit(0)

    platform = 'win' + platform.architecture()[0][:2]

    py_major, py_minor, rest = sys.version.split('.', 2)
    py_major, py_minor = int(py_major), int(py_minor)
    py_version = '{}.{}'.format(py_major, py_minor)

    if py_major == 2:
        print('There is no fix for Python 2.x!')
        sys.exit(2)

    try:
        from PIL import __version__ as PIL_VERSION
        pil_major, pil_minor, rest = PIL_VERSION.split('.', 2)
        pil_major, pil_minor = int(pil_major), int(pil_minor)
        pil_version = '{}.{}'.format(pil_major, pil_minor)
    except ImportError:
        pil_major, pil_minor, pil_version = 0, 0, '???'

    print('Detected system: {}, Python {}, Pillow {}'.format(platform, py_version, pil_version))
    print()

    if pil_major > 6 or (pil_major == 6 and pil_minor >= 1):
        print('No need to update Pillow!')
        sys.exit(0)

    package = packages.get('{}-{}'.format(platform, py_version))
    if package is None:
        print('No update package found for your system!')
        sys.exit(4)

    print('Found package: {}'.format(package))

    print('Type "yes" to {} Pillow 6.1.0.dev0: '.format('update' if py_version == '???' else 'install'), end='')
    response = input()
    print()

    if response != 'yes':
        print('Install cancelled!')
        sys.exit(1)

    try:
        import pip
    except ImportError:
        print('PIP not found. PIP is required to update Pillow!')
        sys.exit(3)

    print('Invoking PIP...')

    subprocess.call([sys.executable, "-m", "pip", "install", package])
