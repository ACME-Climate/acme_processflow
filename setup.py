from setuptools import find_packages, setup
from processflow.version import __version__

setup(
    name="processflow",
    version=__version__,
    author="Sterling Baldwin",
    author_email="baldwin32@llnl.gov",
    description="E3SM Automated workflow for handling post processing and " 
                "diagnostic jobs for raw model data",
    packages=['processflow', 'processflow.jobs', 'processflow.lib'],
    package_dir={'processflow': 'processflow'},
    include_package_data=True,
    entry_points={'console_scripts': ['processflow = processflow.__main__:main']})
