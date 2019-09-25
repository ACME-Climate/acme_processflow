.. processflow documentation master file

***************************
Processflow's documentation
***************************

What is the processflow?
========================

The processflow is a command line tool to automatically run post
processing and diagnostic jobs for E3SM model output.

The tool takes a single configuration files and runs a series of
data transfer and processing jobs on any amount of model output,
running the jobs on any number of set lengths.

Processflow sets up the required regridding and timeseries jobs
needed by the various diagnostics, repeated at the users defined
frequency. This allows users to easily run hundreds of regridding
and diagnostics jobs over centuries of model output. Additionally
processflow allows for model-to-model diagnostic comparisons.

Once the diagnostics complete, processflow transfers the plots
to a hosting directory for easy viewing, and emails the user with
a report of both links as well as paths to the output.

**Jobs:**

* Regridded climatology generation
* Regridded model output for atm, lnd, and mpas data
* Time series variable extraction
* AMWG diagnostics
* A-Prime diagnostics
* E3SM diagnostics
* MPAS-Analysis diagnostics


**System Dependencies:**
If installing the processflow from scratch on a new system, the following
utilities will need to be in place. Most systems that E3SM runs on should
already have these installed.


* Anaconda_
* Slurm_
* APACHE_

.. _Anaconda: https://www.continuum.io/downloads
.. _Slurm: https://slurm.schedmd.com/
.. _NCL: https://www.ncl.ucar.edu/
.. _APACHE: https://www.digitalocean.com/community/tutorials/how-to-configure-the-apache-web-server-on-an-ubuntu-or-debian-vps


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   quickstart
   configuration
   example_config


Output
======

The processflow will create the required input and output directories
based on the project_path option in the config. (:ref:`global_config`).
A copy of the config used to generate the processflow run will be copied
into the /input directory.

Below is an example of the project directory structure.

::

    project_path
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
