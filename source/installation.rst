.. _installation:

************
Installation
************

This guide assumes your system already has the prerequisit dependencies.

* Anaconda_
* Slurm_
* Globus_
* NCL_
* APACHE_

.. _Anaconda: https://www.continuum.io/downloads
.. _Slurm: https://slurm.schedmd.com/
.. _Globus: https://www.globus.org/
.. _NCL: https://www.ncl.ucar.edu/
.. _APACHE: https://www.digitalocean.com/community/tutorials/how-to-configure-the-apache-web-server-on-an-ubuntu-or-debian-vps

Once these are setup, the installation for the acme_workflow is straightforward.

Note:
_____
All these commands assume you're using a bash environment. Other shells may not work correctly with conda

.. code-block:: bash

    wget https://raw.githubusercontent.com/ACME-Climate/acme_processflow/master/env.yml
    conda create --name <SOME_ENVIRONMENT_NAME> --file env.yml
    source activate <SOME_ENVIRONMENT_NAME>


If you already have an installation and want to upgrade, first source your environment and then run:

.. code-block:: bash

    conda update -c acme -c conda-forge -c uvcdat processflow

Or upgrade from the nightly:

.. code-block:: bash

    conda update -c acme/label/nightly -c acme -c conda-forge -c uvcdat processflow

Instructions on configuration and execution can be found here :ref:`Quickstart`
