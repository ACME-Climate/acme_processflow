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
   configuration
   transfer
   amwg
   ncclimo
   aprime
   acme_diags
   sample


Output
======

During the processflow run it will create the required input/output directories based on the project_path config option. The only file that needs to be in place before the run is the config file for that run, which 
will be copied into the input directory. Once the run has completed the directories will have the following structure:

( this example was run with all the diagnostics on 100 years with frequency = 5, 100 )
.. code-block:: bash


    ├── input
    │   ├── atm
    │   ├── ice
    │   ├── mpas
    │   ├── ocn
    │   ├── processflow.db
    │   ├── rest
    │   └── run.cfg
    └── output
        ├── diags
        │   └── fv129x256
        │       ├── amwg [60 entries]
        │       ├── a-prime [21 entries]
        │       └── e3sm_diags [21 entries]
        ├── file_list.txt
        ├── pp
        │   ├── fv129x256
        │   │   ├── climo
        │   │   │   ├── 100yr [17 entries]
        │   │   │   └── 5yr [340 entries]
        │   │   └── ts
        │   │       └── monthly
        │   │           ├── 100yr [14 entries]
        │   │           └── 5yr [280 entries]
        │   └── ne30
        │       ├── climo
        │       │   ├── 100yr [17 entries]
        │       │   └── 5yr [340 entries]
        │       └── ts
        │           └── monthly
        │               ├── 100yr [14 entries]
        │               └── 5yr [280 entries]
        ├── run_scripts [200 entries]
        ├── run_state.txt
        └── tmp
            ├── amwg [21 entries]
            ├── aprime [21 entries]
            └── e3sm_diags [21 entries]
