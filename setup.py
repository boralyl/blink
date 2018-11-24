import os
from setuptools import setup


# Use exec so pip can get the version before installing the module
version_filename = os.path.abspath(os.path.join(
    os.path.dirname(__file__), 'blink', '_version.py'))
with open(version_filename, 'r') as vf:
    exec(compile(vf.read(), version_filename, 'exec'), globals(), locals())

readme_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), 'README.md'))
with open(readme_path, 'r') as fp:
    long_description = fp.read()

setup(
    name='blink',
    version=__version__,  # noqa -- flake8 should ignore this line
    description=('This module allows one to manage their Blink Home Security '
                 'System.'),
    long_description=long_description,
    long_description_content_type='text/x-rst',
    url='https://github.com/boralyl/blink',
    license='MIT',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.6',
    ],
    keywords=['python', 'blink'],
    author='boralyl',
    packages=[
        'blink',
    ],
    install_requires=[
        'python-dateutil >= 2.7.5, < 3.0.0',
        'pyyaml >= 3.13, < 4.0.0',
        'requests >= 2.20.1, < 3.0.0',
        'six',
    ],
    extras_require={
        'tests': [
            'coverage >= 4.5.2, < 5.0.0',
            'flake8 >= 3.6.0, < 4.0.0',
            'mock >= 2.0.0, < 3.0.0',
            'pytest >= 4.0.1, < 5.0.0',
            'requests-mock >= 1.5.2, < 2.0.0',
        ],
    },
)
