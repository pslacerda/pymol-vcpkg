#!/usr/bin/env python3

from os import path
import os
import time
import subprocess
import atexit


def run(args, **kwargs):
    print('>>>>>')
    print('>>>>>', args)
    print('>>>>>')
    subprocess.check_call(args, shell=True, stderr=subprocess.STDOUT, **kwargs)

def get_output(args, **kwargs):
    return subprocess.check_output(args, shell=True, stderr=subprocess.STDOUT, **kwargs).decode()

def concat(l):
    return ' '.join(l)


pymol = 'v2.3.0'
python = '3.7'
target = 'x64-linux'

vcpkg_pkgs = concat([
    'opengl', 'glew', 'freeglut', 'libpng', 'freetype', 'libxml2',
    'glm', 'catch2',
    #'glut', 'osx-frameworks', 'libxml2', 'msgpack',
])
conda_pkgs = concat(['pyqt', 'numpy', 'scipy', 'pandas', 'matplotlib'])
pip_pkgs = concat(['git+https://github.com/schrodinger/pmw-patched.git'])

packaging_pkgs = concat([
    'nuitka', 'conda-pack',
])

root_dir = path.abspath(path.dirname(__file__))
os.chdir(root_dir)
timestamp = str(int(time.time()))
tag = f'pymol{pymol[1:]}-python{python}-{target}-{timestamp}'
vcpkg_install = path.join(root_dir, 'vcpkg', tag)

@atexit.register
def print_output_tag():
    print('>>>>> output tag:', tag, '<<<<<')


if not path.exists('.initialized'):
    run('./vcpkg/bootstrap-vcpkg.sh')
    run('./vcpkg/vcpkg integrate install')
    run('git submodule update --init --recursive')
    if 'linux' in target:
        run('sudo dnf install '
            'mesa-libGL-devel libXi-devel mesa-libGL mesa-libGLU-devel '
            'libXrandr-devel libXxf86vm-devel')
    open('.initialized', 'w').close()

run('git submodule update --recursive --remote')
run(f'git -C pymol-open-source checkout {pymol}')

run(f'vcpkg/vcpkg install --triplet {target} {vcpkg_pkgs}')
run(f'vcpkg/vcpkg export --triplet {target} --raw --output={tag} {vcpkg_pkgs}')
run(f'conda create -y -n {tag} python={python}')
run(f'conda install -y -n {tag} {conda_pkgs}')
run(f'conda run -n {tag} pip install {pip_pkgs} {packaging_pkgs}')

os.chdir(path.join(root_dir, 'pymol-open-source'))
prefix_path = path.join(vcpkg_install, 'installed', 'x64-linux')
run(f'conda run -n {tag} python setup.py install --use-msgpack=no', env={
    'PATH': os.environ['PATH'],
    'PREFIX_PATH': prefix_path,
})

env_dir = path.dirname(path.dirname(get_output(f"conda run -n {tag} which python")))

if 'linux' in target:
    pymol_cmd_path = path.join(env_dir, 'bin', 'pymol')
    with open(pymol_cmd_path, 'w') as pymol_cmd_file:
        pymol_cmd_file.write(f"""#!/bin/sh
ROOT="$(readlink -f $(dirname $0)/../)"
export PYMOL_PATH="$ROOT/lib/python{python}/site-packages/pymol/pymol_path"
"$ROOT/bin/python" "$ROOT/lib/python{python}/site-packages/pymol/__init__.py" "$@"
""")
elif 'windows' in target:
    pass


dist_dir = path.join(root_dir, 'dist')
os.makedirs(path.join(root_dir, 'dist'), 0o755, True)
output_package = path.join(dist_dir, f'{tag}.tar.gz')
run(f'conda run -n {tag} conda-pack --n-threads -1 --compress-level 9 --output {output_package}')
