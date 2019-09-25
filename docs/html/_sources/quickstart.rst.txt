.. _quickstart:

***********
Quick Start
***********

This is a guide for a new user on a system thats already been properly setup.
New users please referece to guide :ref:`Installation`.


Processflow install
-------------------

You will need to first create an anaconda environment with the depedencies
and install the processflow. Once conda has install all the python modules,
create a run configuration file from the default and edit it to suit your case.
You can find an :ref:`example_config` here.

This install command will create a new anaconda environment with the
latest stable release.

::

    conda create --name processflow -c conda-forge -c e3sm -c cdat/label/v81 processflow
    conda activate processflow

Use the following command to get the latest nightly build.

::

    conda create --name processflow_nightly -c conda-forge -c e3sm/label/nightly -c e3sm -c cdat/label/v81 processflow
    conda activate processflow_nightly


Once you have the processflow installed, the next step is creating your
run configuration file. See :ref:`configuration` on how to setup your run
config.

Configuration
-------------

See `here for real life configuration examples <https://github.com/E3SM-Project/processflow/tree/master/samples>`_

Get a copy of the example config, and edit its keys to fit your case.
You can get a copy of the example here:

::

    wget https://raw.githubusercontent.com/E3SM-Project/processflow/master/run.cfg

For a complete explanation of each config key, see the :ref:`Configuration`
guide.

For an example config with all the available options turned on
see the :ref:`example_config`


Execution
---------

Running the processflow is simple. Once your config is setup, simply
execute the following command:

::

    processflow.py run.cfg


Once diagnostic output has been created, it will be moved to the host
location (if img hosting is turned on). The web directories on NERSC and
LLNL machines are password protected, credentials to view the output can
be found here: https://acme-climate.atlassian.net/wiki/spaces/ATM/pages/41353486/How+to+run+AMWG+diagnostics+package?preview=%2F41353486%2F42730119%2Fcredentials.png

.. _machine_specific_config:

Machine Specific Configuration
------------------------------

Each of the E3SM supported machines has a slightly different
setup for where they store input files and host output.

LCRC (Blues/Anvil)
------------------

All jobs should have the following keys added to
their config when running on blues:

::

    [[[custom_args]]]
        --partition = acme-centos7
        --account = condo

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
            reference_data_path = /lcrc/group/acme/diagnostics/obs_for_e3sm_diags/climatology/

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
        img_host_server = acme-viewer.llnl.gov
        host_directory = /var/www/acme/acme-diags/<YOUR_USERNAME>/
        url_prefix = <YOUR_USERNAME>

    [post-processing]
        [[climo]]
            regrid_map_path = /export/zender1/data/maps/<YOUR_REGRID_MAP>

    [diags]
        [[e3sm_diags]]
            reference_data_path = /p/cscratch/acme/data/obs_for_acme_diags

        [[amwg]]
            diag_home = /p/cscratch/acme/amwg/amwg_diag

        [[aprime]]
            aprime_code_path = /p/cscratch/acme/data/a-prime

NERSC (cori)
------------

NOTE: All jobs here need to be submitted to the "regular"
partition, using the "e3sm" account.
::

    [[[custom_args]]]
        --partition = regular
        --account = acme
        -C = haswell

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

    [diags]
        [[e3sm_diags]]
            reference_data_path = /global/project/projectdirs/acme/acme_diags/obs_for_e3sm_diags

        [[amwg]]
            diag_home = /global/project/projectdirs/acme/diagnostics/amwg/amwg_diag

        [[aprime]]
            aprime_code_path = <you have to clone the a-prime repo and set it up yourself>
