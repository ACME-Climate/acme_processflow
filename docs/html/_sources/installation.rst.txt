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
.. _Globus: https://www.globus.org/ (only required if moving data)
.. _NCL: https://www.ncl.ucar.edu/ (only required if running AMWG)
.. _APACHE: https://www.digitalocean.com/community/tutorials/how-to-configure-the-apache-web-server-on-an-ubuntu-or-debian-vps (only required if hosting images)

Once these are setup, the installation for the processflow is straightforward. If you're running on acme1, aims4, or Edison you shouldnt have to setup
any of these services as they should all be running. If you're running and already have your data local, you dont need globus.

Note
----

All these commands assume you're using a bash environment. Other shells may not work correctly with conda

.. code-block:: bash

    conda create --name processflow -c e3sm -c cdat/label/nightly -c conda-forge -c cdat processflow
    conda activate processflow


If you already have an installation and want to upgrade, first source your environment and then run:

.. code-block:: bash

    conda update -c e3sm -c cdat/label/nightly -c conda-forge -c cdat processflow

Or upgrade from the nightly:

.. code-block:: bash

    conda update -c e3sm/label/nightly -c e3sm -c cdat/label/nightly -c conda-forge -c cdat processflow processflow

Instructions on configuration and execution can be found here :ref:`Quickstart`
