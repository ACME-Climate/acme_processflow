from setuptools import find_packages, setup

setup(
    name="processflow",
    version="2.2.1",
    author="Sterling Baldwin",
    author_email="baldwin32@llnl.gov",
    description="E3SM Automated workflow for handling post processing and diagnostic jobs for raw model data",
    packages=find_packages(
        exclude=["*.test", "*.test.*", "test.*", "test", "*_template.py"]),
    include_package_data=True,
    entry_points={'console_scripts': ['processflow = processflow.__main__:main']})
