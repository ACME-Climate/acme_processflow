.. acme_processflow documentation master file, created by
   sphinx-quickstart on Tue Aug 15 16:44:35 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

********************************
acme_processflow's documentation
********************************

What is the processflow?
===============================

The acme_processflow is a command line tool to automatically run post processing jobs for ACME model output.

The tool takes a single configuration files and runs a series of long running transfer
and processing jobs on any amount of model output, running the set of jobs on any number of set lengths. The output
doesn't have to exist before the tool is run, meaning it can be started at the same time as the model and as data is
generated will transfer it, and start the processing and diagnostics as soon as the first complete set is available.

Transfer jobs will be generated to match the data requirements of the processing jobs, and the processing jobs will 
wait to run until after the data has been made available. Once the diagnostics complete, the tool manages hosting the 
images and emails links with the completed output to the user. 

**Jobs:**

* Globus Transfer
* AMWG diagnostic
* Regridding and Climatologies
* Time series variable extraction
* A-Prime diagnostic
* E3SM diags

Each processing job has an optional number of other jobs it should wait on, for example
AMWG will wait for the regridded climatologies to be generated before starting its
run.

**Shell**

All commands are written for BASH. If you're using tcsh or zsh you will need to first run the `bash` command to enter a bash shell.

**Dependencies:**

* Anaconda_
* Slurm_
* Globus_
* NCL_
* APACHE_
* BASH

.. _Anaconda: https://www.continuum.io/downloads
.. _Slurm: https://slurm.schedmd.com/
.. _Globus: https://www.globus.org/
.. _NCL: https://www.ncl.ucar.edu/
.. _APACHE: https://www.digitalocean.com/community/tutorials/how-to-configure-the-apache-web-server-on-an-ubuntu-or-debian-vps


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   quickstart
   transfer
   amwg
   ncclimo
   aprime
   acme_diags
   sample


Output
======

During the processflow run it will create the required input/output directories. The only file that needs to be in place before the run is the config file for that run, which 
will be copied into the input directory. Once the run has completed the directories will have the following structure:

.. code-block:: bash


    project_path
    ├── input
    │   ├── atm
    │   │   ├── 20170915.beta2.A_WCYCL1850S.ne30_oECv3_ICG.edison.cam.h0.0001-01.nc
    │   │   ├── .........
    │   │   └── 20170915.beta2.A_WCYCL1850S.ne30_oECv3_ICG.edison.cam.h0.0060-12.nc
    │   ├── case_scripts
    │   ├── ice
    │   │   ├── mpascice.hist.am.timeSeriesStatsMonthly.0051-01-01.nc
    │   │   ├── .........
    │   │   └── mpascice.hist.am.timeSeriesStatsMonthly.0060-12-01.nc
    │   ├── mpas
    │   │   ├── mpas-cice_in
    │   │   └── mpas-o_in
    │   ├── ocn
    │   │   ├── mpaso.hist.am.timeSeriesStatsMonthly.0051-01-01.nc
    │   │   ├── ........
    │   │   └── mpaso.hist.am.timeSeriesStatsMonthly.0058-11-01.nc
    │   ├── rest
    │   │   └── mpaso.rst.0052-01-01_00000.nc
    │   └── run.cfg
    └── output
        ├── amwg_diag
        │   ├── 0051-0055
        │   ├── 0051-0060
        │   └── 0056-0060
        ├── aprime_diags
        │   ├── 0051-0055
        │   └── 0056-0060
        ├── climo
        │   ├── 10yr
        │   │   ├── 20170915.beta2.A_WCYCL1850S.ne30_oECv3_ICG.edison_01_005101_006001_climo.nc
        │   │   ├── ..........
        │   │   └── 20170915.beta2.A_WCYCL1850S.ne30_oECv3_ICG.edison_12_005112_006012_climo.nc
        │   └── 5yr
        │       ├── 20170915.beta2.A_WCYCL1850S.ne30_oECv3_ICG.edison_01_005101_005501_climo.nc
        │       ├── ..........
        │       └── 20170915.beta2.A_WCYCL1850S.ne30_oECv3_ICG.edison_SON_005109_005511_climo.nc
        ├── climo_regrid
        │   ├── 20170915.beta2.A_WCYCL1850S.ne30_oECv3_ICG.edison_01_005101_005501_climo.nc
        │       ├── ..........
        │   └── 20170915.beta2.A_WCYCL1850S.ne30_oECv3_ICG.edison_12_005112_005512_climo.nc
        ├── e3sm_diags
        │   ├── 0051-0055
        │   └── 0056-0060
        ├── file_list.txt
        ├── monthly
        │   ├── 10yr
        │       ├── ..........
        │   └── 5yr
        │       ├── ..........
        ├── run_scripts
        │   ├── ncclimo_0051_0055
        │   ├── ..........
        │   └── timeseries_0056_0060.out
        ├── run_state.txt
        │   └── e3sm_diags
        │       ├── 0051-0055
        │       └── 0056-0060
        ├── workflow.error
        └── workflow.log
