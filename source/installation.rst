.. _installation:

************
Installation
************

This guide assumes your system already has the prerequisit dependencies.

* Anaconda_
* Slurm_
* Globus_ (only required if moving data)
* APACHE_ (only required if hosting images)

.. _Anaconda: https://www.continuum.io/downloads
.. _Slurm: https://slurm.schedmd.com/
.. _Globus: https://www.globus.org/ 
.. _APACHE: https://www.digitalocean.com/community/tutorials/how-to-configure-the-apache-web-server-on-an-ubuntu-or-debian-vps

Once these are setup, the installation for the processflow is straightforward. If you're running on acme1, aims4, or Edison you shouldnt have to setup
any of these services as they should all be running. If you already have your data local, you dont need globus.

Note
----

All these commands assume you're using a bash environment. Other shells may not work correctly with conda.

::

    conda create --name processflow -c e3sm -c cdat/label/nightly -c conda-forge -c cdat processflow
    conda activate processflow


If you already have an installation and want to upgrade, first source your environment and then run:

::

    conda update -c e3sm -c cdat/label/nightly -c conda-forge -c cdat processflow

Or upgrade from the nightly:

:: 

    conda update -c e3sm/label/nightly -c e3sm -c cdat/label/nightly -c conda-forge -c cdat processflow

Instructions on configuration and execution can be found here :ref:`Quickstart`
