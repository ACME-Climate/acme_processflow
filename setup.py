import sys
from setuptools import find_packages, setup

data_files = [(sys.prefix + '/share/processflow/resources',
               ['resources/e3sm_diags_template_vs_model.py',
                'resources/e3sm_diags_template_vs_obs.py',
                'resources/amwg_template_vs_model.csh',
                'resources/amwg_template_vs_obs.csh',
                'resources/env_loader.bash',
                'resources/aprime_template_vs_obs.bash'])]

setup(
    name="e3sm_processflow",
    version="2.2.1",
    author="Sterling Baldwin",
    author_email="baldwin32@llnl.gov",
    description="E3SM Automated workflow for handling post processing and diagnostic jobs for raw model data",
    scripts=["processflow"],
    packages=find_packages(
        exclude=["*.test", "*.test.*", "test.*", "test", "*_template.py"]),
    data_files=data_files)
