import sys
from setuptools import find_packages, setup

data_files = [(sys.prefix + '/share/processflow/resources',
               ['resources/e3sm_diags_template.py',
                'resources/amwg_template.csh',
                'resources/config_template.json',
                'resources/aprime_template.bash',
                'resources/acme-banner_1.jpg',
                'resources/aprime_index.html',
                'resources/aprime_submission_template.sh',
                'resources/e3sm_diags_submission_template.sh',
                'resources/amwg_submission_template.sh'])]

setup(
    name="acme_processflow",
    version="1.0.3",
    author="Sterling Baldwin",
    author_email="baldwin32@llnl.gov",
    description="ACME Automated Processflow for handling post processing jobs for raw model data",
    scripts=["processflow.py"],
    packages=find_packages(
        exclude=["*.test", "*.test.*", "test.*", "test", "*_template.py"]),
    data_files=data_files)
