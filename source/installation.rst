.. _installation:

************
Installation
************

This guide assumes your system already has the prerequisit dependencies.

* Anaconda_
* Slurm_
* APACHE_ (only required if hosting images)

.. _Anaconda: https://www.continuum.io/downloads
.. _Slurm: https://slurm.schedmd.com/
.. _APACHE: https://www.digitalocean.com/community/tutorials/how-to-configure-the-apache-web-server-on-an-ubuntu-or-debian-vps

Once these are setup, the installation for the processflow is straightforward.
If you're running on acme1, compy, or Cori you shouldnt have to setup
any of these services as they should all be running.

Note
----

All these commands assume you're using a bash environment. Other shells may not
work correctly with conda.

::

    conda create --name processflow -c conda-forge -c e3sm -c cdat/label/v81 processflow
    conda activate processflow


If you already have an installation and want to upgrade, first source your
environment and then run:

::

    conda update -c conda-forge -c e3sm -c cdat/label/v81 processflow

Or upgrade from the nightly:

::

    conda update -c conda-forge -c e3sm/label/nightly -c e3sm -c cdat/label/v81 processflow

Instructions on configuration and execution can be found here :ref:`Quickstart`
