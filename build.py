#!/usr/bin/env python3

from os import path
import os
import time
import subprocess


def run(args, **kwargs):
    print('\n\n\n>>>>> ', args)
    subprocess.check_call(args, shell=True, stderr=subprocess.STDOUT, **kwargs)


def concat(l):
    return ' '.join(l)


pymol = 'v2.3.0'
python = '3.7'
target = 'x64-linux'

vcpkg_pkgs = concat([
    'opengl', 'glew', 'freeglut', 'libpng', 'freetype', 'libxml2',
    'glm', 'catch2'])
conda_pkgs = concat(['pyqt'])
pip_pkgs = concat(['git+https://github.com/schrodinger/pmw-patched.git'])
#optionals = ['glut', 'osx-frameworks', 'libxml2', 'msgpack']

root_dir = path.abspath(path.dirname(__file__))
os.chdir(root_dir)
timestamp = str(int(time.time()))
tag = f'pymol-build-{timestamp}'
vcpkg_install = path.join(root_dir, 'vcpkg', tag)
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
run(f'conda run -n {tag} pip install {pip_pkgs}')

os.chdir(path.join(root_dir, 'pymol-open-source'))
prefix_path = path.join(vcpkg_install, 'installed', 'x64-linux')
run(f'conda run -n {tag} python setup.py install --use-msgpack=no', env={
    'PATH': os.environ['PATH'],
    'PREFIX_PATH': prefix_path,
})
