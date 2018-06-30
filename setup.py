import ast
import pathlib
import sys
from setuptools import find_packages, setup


def read_version():
    """
    Read the version from `asterios_client/__version__.py` without import
    module to avoid side effect.
    """
    module_src = (
        pathlib.Path(__file__).parent / "asterios_client" / "__version__.py"
    ).read_text()
    for statment in ast.parse(module_src).body:
        if isinstance(statment, ast.Assign):
            if statment.targets[0].id == "__version__":
                version = statment.value.s
                break
    else:
        exit(
            "The `__version__` variable is not defined"
            " in the `asterios_client.__version__` module"
        )

    return version


setup(
    name='asterios_client',
    version=read_version(),
    description='Asterios client',
    keywords='escape game server Asterios client',
    author='Vincent Maillol',
    author_email='vincent.maillol@gmail.com',
    url='https://github.com/maillol/asterios_client',
    license='GPLv3',
    packages=['asterios_client'] + [
        "asterios_client.{}".format(subpackage)
        for subpackage in find_packages(where="./asterios_client")
    ],
    classifiers=[
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)'
    ],
    python_requires='>=3.5'
)
