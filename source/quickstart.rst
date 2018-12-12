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

::

    conda create --name processflow -c e3sm -c cdat/label/nightly -c conda-forge -c cdat processflow
    conda activate processflow

Use the following command to get the latest nightly build.

:: 

    conda create --name processflow_nightly -c e3sm/label/nightly -c e3sm -c cdat/label/nightly -c conda-forge -c cdat processflow
    conda activate processflow_nightly


Once you have the processflow installed, the next step is creating your run configuration file. See :ref:`configuration` on how to setup your run config. You can find a :ref:`Sample` configuration here.

Configuration
-------------

See `here for real life configuration examples <https://github.com/E3SM-Project/processflow/tree/master/samples>`_

Get a copy of the example config, and edit its keys to fit your case. You can get a copy of the example here:

::

    wget https://raw.githubusercontent.com/E3SM-Project/processflow/master/run.cfg

For a complete explanation of each config key, see the :ref:`Configuration` guide.

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

.. _machine_specific_config:

Machine Specific Configuration
------------------------------

Each of the E3SM supported machines has a slightly different setup for where they store input files and host output.

LCRC (Blues/Anvil)
------------------

::

    [global]
        project_path = /lcrc/group/acme/<YOUR_USERNAME>/<YOUR_PROJECT>

    [img_hosting]
        img_host_server = web.lcrc.anl.gov
        host_directory = /lcrc/group/acme/public_html/diagnostic_output/<YOUR_USERNAME>
        url_prefix = /public/e3sm/diagnostic_output/<YOUR_USERNAME>
    
    [post-processing]
        [[climo]]
            regrid_map_path = ~zender/data/maps/<YOUR_REGRID_MAP>
    
    [diags]
        [[e3sm_diags]]
            reference_data_path = /lcrc/group/acme/diagnostics/obs_for_acme_diags

        [[amwg]]
            diag_home = /lcrc/group/acme/amwg/amwg_diag

        [[aprime]]
            aprime_code_path = /lcrc/group/acme/diagnostics/a-prime/code
    
LLNL (acme1/aims4)
------------------

::

    [global]
        project_path = /p/user_pub/e3sm/<YOUR_USERNAME>/<YOUR_PROJECT>
    
    [img_hosting]
        img_host_server = Either acme-viewer.llnl.gov or aims4.llnl.gov
        host_directory = /var/www/acme/acme-diags/<YOUR_USERNAME>/
        url_prefix = <YOUR_USERNAME>
    
    [post-processing]
        [[climo]]
            regrid_map_path = /space2/zender1/data/maps/<YOUR_REGRID_MAP>
    
    [diags]
        [[e3sm_diags]]
            reference_data_path = /p/cscratch/acme/data/obs_for_acme_diags

        [[amwg]]
            diag_home = /p/cscratch/acme/amwg/amwg_diag

        [[aprime]]
            aprime_code_path = /p/cscratch/acme/data/a-prime

NERSC (edison)
--------------

NOTE: All jobs here need to be submitted to the "regular" partition, using the "acme" account.

::

    [global]
        project_path = /global/project/projectdirs/acme/<YOUR_USERNAME>/<YOUR_PROJECT>
    
    [img_hosting]
        img_host_server = portal.nersc.gov
        host_directory = /project/projectdirs/acme/www/<YOUR_USERNAME>
        url_prefix = project/acme/<YOUR_USERNAME>
    
    [post-processing]
        [[climo]]
            regrid_map_path = ~zender/data/maps/<YOUR_REGRID_MAP>
            [[[custom_args]]]
                --partition = regular
                --account = acme
    
    [diags]
        [[e3sm_diags]]
            reference_data_path = /p/cscratch/acme/data/obs_for_acme_diags
            [[[custom_args]]]
                --partition = regular
                --account = acme

        [[amwg]]
            diag_home = /global/project/projectdirs/acme/diagnostics/amwg
            [[[custom_args]]]
                --partition = regular
                --account = acme

        [[aprime]]
            aprime_code_path = /p/cscratch/acme/data/a-prime
            [[[custom_args]]]
                --partition = regular
                --account = acme
