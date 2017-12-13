.. _quickstart:

***********
Quick Start
***********

This is a guide for a new user on a system thats already been properly setup. For new users starting from scratch please referece to the
:ref:`Installation` guide. 


Anaconda
--------

You will need to first create an anaconda environment with the depedencies and install the processflow. Once conda has install all the python modules, create a run configuration file from the 
default and edit it to suit your case. You can find a :ref:`Sample` configuration here.

.. code-block: bash

    conda create -n processflow -c uvcdat -c conda-forge -c acme -c lukasz processflow
    source activate processflow


Run Configuration
-----------------

The acme_processflow config file contains all settings required to setup a run. Although the config file has many options, most of them
are only useful in non-default environments or to advanced users. For a basic run, the only keys that need to be changed are:


**project_path**
The root path to be created on the local machine for all local storage. All model data used as input will be saved in project_path/input, and all job output will be stored in project_path/output

**source_path**
This is the path to look for data on the remote machine. This should be the root directory for the simulation, below which will be /run and /archive directories.

**simulation_start_year**
The start year of the simulation. For example if the first year of the simulation output is 0100, put 100. If the first year is 0001, out 1. Note that since E3SM numbers its years as a 1 indexed array, the first year should be 1, not 0.

**simulation_end_year**
The expected end year. This can be set to any year while the simulation is still starting, and the acme_processflow will continuously poll for new data and start jobs as the data is made available.

**exeriment**
The name of the experiment, based on the ACME convention for naming the file output. For example: 20170313.beta1_02.A_WCYCL1850S.ne30_oECv3_ICG.edison

**set_frequency**
The acme_processflow breaks the simulation into groups based on how much data you want the jobs to run on. 
For example if you wanted AMWG to run on every 10 years, but also on every 50 years, you could have set_frequency = 10, 50, 
and for every group of 10 years and 50 years you would get the jobs for that length run. 
In this example, with 50 years of output, you would get sets from 1-10, 11-20, 21-30, 31-40, 41-50, and 1-50.

**set_jobs**
Which jobs to run on which sets. This allows you to have different subsets of jobs run on different set lengths. 
If you dont want a job to run at all simply remove it from the list.

An example:

[[set_jobs]]
    # this will run ncclimo for both 5 and 10
    ncclimo = 5, 10
    # this will run time series only at 10
    timeseries = 10
    # this will run amwg only at 5
    amwg = 5
    # this will turn off the aprime diags by commenting it out
    # aprime_diags = 5
    e3sm_diags = 10



Execution
---------

The acme_processflow has two run modes, interactive and headless. In headless mode the current run status is written out to a file named run_state.txt under the output directory.


.. code-block:: bash

    usage: processflow.py [-h] [-c CONFIG] [-u] [-l LOG] [-n] [-m] [-f]
                      [-r RESOURCE_DIR]

    optional arguments:
    -h, --help            show this help message and exit
    -c CONFIG, --config CONFIG
                            Path to configuration file.
    -u, --ui              Turn on the GUI.
    -l LOG, --log LOG     Path to logging output file.
    -n, --no-cleanup      Don't perform post run cleanup. This will leave all
                            files in place.
    -m, --no-monitor      Don't run the remote monitor or move any files over
                            globus.
    -f, --file-list       Turn on debug output of the internal file_list so you
                            can see what the current state of the model files are
    -r RESOURCE_DIR, --resource-dir RESOURCE_DIR
                            Path to custom resource directory

Once you've configured your run, execute this command to start in interactive mode.

.. code-block:: bash

    processflow.py -c run.cfg

When run in interactive mode, the acme_processflow will exit if the terminal window is closed. For long running jobs, the best run method is to make sure the source and destination globus nodes have been activated with your credentials, and then run

.. code-block:: bash

    nohup processflow.py -c /PATH/TO/YOUR/CONFIG &

Once the run starts, you will be prompted to authenticate with globus. Simply copy the address and paste into your browser. 
You will be presented with a page to choose which OAuth provided to use, its recommended that you use the default globus ID provider.

Once you have entered your credentials and logged in, you will be given a randomly generated key, copy that key and paste it into the terminal prompt

Once you have logged into globus, each data node will need to be activated with your account. This activation can last for days, but periodically needs to be re-run. 
If the node needs to be activated you will be prompted, if your credentials are still cached on the node this step will be skipped.

Once a run starts in interactive mode, you should see the job sets listed, and the jobs should populate. When all the jobs finish, you will be emailed with links to the diagnostic output.

Credentials to view the output can be found here: https://acme-climate.atlassian.net/wiki/spaces/ATM/pages/41353486/How+to+run+AMWG+diagnostics+package?preview=%2F41353486%2F42730119%2Fcredentials.png