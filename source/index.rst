.. processflow documentation master file, created by
   sphinx-quickstart on Tue Aug 15 16:44:35 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

***************************
Processflow's documentation
***************************

What is the processflow?
===============================

The processflow is a command line tool to automatically run post processing and diagnostic jobs for E3SM model output.

The tool takes a single configuration files and runs a series of data transfer
and processing jobs on any amount of model output, running the jobs on any number of set lengths.

Transfer jobs will be generated to match the data requirements of the processing jobs, and the processflow will wait
to run jobs until after the data transfer has completed. Once the diagnostics complete, the tool transfers the plots to a hosting directory, 
and emails links with the completed output to the user. 

**Jobs:**

* Globus and SFTP file transfer
* Regridded climatology generation
* Time series variable extraction
* atm, lnd, and ocn regridding
* AMWG diagnostic
* A-Prime diagnostic
* E3SM diags


**System Dependencies:**
If installing the processflow from scratch on a new system, the following utilities will need to be in place. 
Most systems that E3SM runs on should already have these installed.


* Anaconda_
* Slurm_
* Globus_ (Only needed if using globus transfer)
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
   sample


Output
======

The processflow will create the required input and output directories based on the project_path option in the config. 
(:ref:`global_config`). A copy of the config used to generate the processflow run will be copied into the /input directory.

Below is an example of the project directory structure.

::

    project_path
    ├── input
    |   ├── case.id.1
    │   │     ├── atm 
    │   │     ├── ice
    │   │     ├── mpas
    │   │     ├── ocn
    │   │     └── rest
    │   ├── case.id.2
    │   │      ├── atm
    │   │      ├── ice
    │   │      ├── mpas
    │   │      ├── ocn
    │   │      └── rest
    │   └── run.cfg
    └── output
        ├── file_list.txt
        ├── processflow.log
        ├── state.txt
        ├── scripts
        ├── diags
        |   ├── case.id.1
        |   |     ├── aprime
        |   |     |     ├── case.id.1_vs_obs
        |   |     ├── e3sm_diags
        |   |     |     ├── case.id.1_vs_obs
        |   |     |     └── case.id.1_vs_case.id.2
        |   |     └── amwg
        |   |           ├── case.id.1_vs_obs
        |   |           └── case.id.1_vs_case.id.2
        |   └── case.id.2
        |         ├── aprime
        |         |     └── case.id.2_vs_obs
        |         ├── e3sm_diags
        |         |     └── case.id.2_vs_obs
        |         └── amwg
        |               └── case.id.2_vs_obs
        └── pp
            ├── fv129x256
            │   ├── case.id.1
            │   │   ├── climo
            │   │   │   └── 2yr
            │   │   ├── regrid
            │   │   │   ├── atm
            │   │   │   └── lnd
            │   │   └── ts
            │   │       └── 2yr
            │   └── case.id.2
            │       ├── climo
            │       │   └── 2yr
            │       ├── regrid
            │       │   ├── atm
            │       │   └── lnd
            │       └── ts
            │           └── 2yr
            └── ne30
                ├── case.id.1
                │   ├── climo
                │   │   └── 2yr
                │   └── ts
                │       └── 2yr
                └── case.id.2
                    ├── climo
                    │   └── 2yr
                    └── ts
                        └── 2yr
