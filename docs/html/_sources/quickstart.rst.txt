.. _quickstart:

***********
Quick Start
***********

This is a guide for a new user on a system thats already been properly setup. For new users starting from scratch please referece to the
:ref:`Installation` guide. 


Processflow install
-------------------

You will need to first create an anaconda environment with the depedencies and install the processflow. Once conda has install all the python modules, create a run configuration file from the 
default and edit it to suit your case. You can find a :ref:`Sample` configuration here.

This install command will create a new anaconda environment with the latest stable release.

.. code-block: bash

    conda create --name processflow -c e3sm -c cdat/label/nightly -c conda-forge -c cdat processflow
    conda activate processflow

Use the following command to get the latest nightly build.

.. code-block: bash

    conda create --name processflow_nightly -c e3sm/label/nightly -c e3sm -c cdat/label/nightly -c conda-forge -c cdat processflow
    conda activate processflow_nightly


Once you have the processflow installed, the next step is creating your run configuration file. See :ref:`configuration` on how to setup your run config. You can find a :ref:`Sample` configuration here.


Execution
---------

Running the processflow is extremely simple. Once your config is setup, simply execute the following command:

::

    processflow.py -c /path/to/your/run.cfg


Once the run starts, you may be prompted to authenticate with globus (if using globus to transfer files), or your ssh credentials (is using sftp to transfer files).


Once you have logged into globus, each data node will need to be activated with your account. 
This activation can last from days to weeks depending on the nodes configuration, but periodically needs to be re-run. 
If a node needs to be activated the processflow will notify you and wait. 


Once diagnostic output has been created, it will be moved to the host location (if img hosting is turned on). The web directories on NERSC and LLNL machines are password protected, credentials to view the output can be found here: https://acme-climate.atlassian.net/wiki/spaces/ATM/pages/41353486/How+to+run+AMWG+diagnostics+package?preview=%2F41353486%2F42730119%2Fcredentials.png