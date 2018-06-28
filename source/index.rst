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

* Globus Transfer
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

( this example was run with all the diagnostics on 100 years with frequency = 5, 100, with the ne30 and fv129x256 grids )
.. code-block:: bash

    project_path
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
        │       ├── amwg
        │       ├── a-prime
        │       └── e3sm_diags
        ├── file_list.txt
        ├── pp
        │   ├── fv129x256
        │   │   ├── climo
        │   │   │   ├── 100yr
        │   │   │   └── 5yr
        │   │   └── ts
        │   │       └── monthly
        │   │           ├── 100yr
        │   │           └── 5yr
        │   └── ne30
        │       ├── climo
        │       │   ├── 100yr
        │       │   └── 5yr
        │       └── ts
        │           └── monthly
        │               ├── 100yr
        │               └── 5yr
        ├── run_scripts
        ├── run_state.txt
        └── tmp
            ├── amwg
            ├── aprime
            └── e3sm_diags
