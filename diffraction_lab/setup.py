from setuptools import setup, find_packages

setup(
    name='diffraction-lab',
    version='1.0.0',
    description='衍射仿真软件 - DiffractionLab',
    author='DiffractionLab',
    packages=find_packages(),
    python_requires='>=3.10',
    install_requires=[
        'numpy>=1.24.0',
        'scipy>=1.10.0',
        'PyQt6>=6.5.0',
        'pyqtgraph>=0.13.0',
        'opencv-python>=4.8.0',
        'Pillow>=10.0.0',
        'h5py>=3.9.0',
        'numba>=0.58.0',
        'pydantic>=2.0.0',
        'pyyaml>=6.0',
        'tifffile>=2023.0.0',
    ],
    extras_require={
        'gpu': ['cupy-cuda11x>=12.0.0'],
        'dev': ['pytest>=7.0.0', 'pyinstaller>=6.0.0'],
    },
    entry_points={
        'console_scripts': [
            'diffraction-lab=src.main:main',
        ],
    },
    package_data={
        '': ['config/*.yaml', 'assets/*'],
    },
)
