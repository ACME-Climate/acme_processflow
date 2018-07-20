.. _configuration:

*****************
Run Configuration
*****************


Run configuration is broken into 6 major sections:

    * :ref:`global_config`  options used by all components
    * :ref:`img_hosting` options used for hosting diagnostic output
    * :ref:`simulations` options related to each case being run, and how case-vs-case comparisons should be configured
    * :ref:`post-processing` all options related to post processing jobs
    * :ref:`diags` all options related to diagnostic runs
    * :ref:`data_types` definitions of which data types are required, and how to find data files
    * :ref:`example_config` an example config file

.. _global_config:

global
------

The global section has the following keys: 

    * project_path (string): This is the base of the processflow project directory tree. All input and output will be stored here under project_path/input/ and project_path/output/. Any required directories will be generated.
    * email (string): This is the email address to send notifications to.
    * native_grid_cleanup (bool): This is a boolean flag to denoting if the native grid files produced by post processing jobs should be deleted after all jobs successfully complete
    * local_globus_uuid (string): The local globus transfer nodes unique id. This is optional and only required if using globus for file transfers

**example**
::

    [global]
        project_path = /path/to/local/project
        email = YOUREMAIL@INSTITUTION.DOMAIN
        native_grid_cleanup = False
        local_globus_uuid = a871c6de-2acd-11e7-bc7c-22000b9a448b

.. _img_hosting:

img_hosting
-----------

This is an optional section, only needed if the user would like to turn on web hosting for diagnostic plot output. To turn off output hosting, simply remove this section from the configuration.

    * img_host_server (string): The base url of the webserver, used for constructing the notification email links.
    * host_directory (string): The base directory for where to put output for web hosting, the user must have permission to write here. Directories will be created for each simulation case, with jobs for the case stored below it.
    * url_prefix (string): Notification urls are constructed as https://{img_host_server}/{url_prefix}/{case}/{diagnostic}

**example**
::

    [img_hosting]
        img_host_server = your-web-server.institution.domain
        host_directory = /path/to/where/you/host/your/files/
        url_prefix = /any/statis/url/prefix/you/need/

.. _simulations:

simulations
-----------

This section is used for configuring each case. As many cases can be placed here as the user would like. 
The cases can be very different from each other, use different naming conventions (see data_types), and have their data stored in different file structures. 
The one thing they must all share in common is the start_year and end_year.

    * start_year (int): the first year of data to be used.
    * end_year (int): the last year of data.

**A new section is created for each case, allowing very different configs for the different cases.**

    * [[CASEID]] (string): this should be the full case name e.g. [[20180129.DECKv1b_piControl.ne30_oEC.edison]]
    * short_name (string): a nice short name for the case, this can be any string identifier for this case
    * native_grid_name (string): the name of the native grid used in the land and atmospheric components
    * native_mpas_grid_name (string): the name of the mpas grid
    * data_types (list): which data types should be copied for this case, this must include all data_types needed for jobs this case will be running in a space seperated list. Can be set to 'all' to mean all data types described in the data_types section.
    * job_types (list): which of the job types should be run on this case. Use the keyword 'all' to run all defined jobs on this case.

**transfer_type**
Each simulated case needs to have a transfer type. Transfer_type can be one of three different values, which force certain values to be included for the case:

    * 'local' --> the case must then also have 'local_path,' which is then used to specify the location for each datatype in the data_types section
    * 'sftp' --> the case must then also have 'remote_hostname,' which is the remote server to connect to and 'remote_path'
    * 'globus' --> the case must then also have 'remote_uuid,' which is the globus unique identifier for the remote node, and 'remote_path'. The 'global' section should also include the 'local_globus_uuid' key.

**If running diagnostic jobs, the [[comparisons]] section must be included**
    
This is the list of comparisons between for each case. 
Each case running diagnostics should have an entry here, followed by which other cases it should be compared to. 
This can include the keywords 'all' for all possible comparisons, or 'obs' for model-vs-obs comparisons. The 'all' keyword will add comparisons with each other case as well as model-vs-obs.
    
**example**
::

    [[comparisons]]
        case_1 = obs, case_2
        case_2 = case_3
        case_3 = all

In this example the following comparison diagnostics jobs will be generated:

    * case_1-vs-obs, case_1-vs-case_2
    * case_2-vs-case_3
    * case_3-vs-case_1, case_3-vs-case_2, case_3-vs-obs

Note how case_2-vs-case_3 and case_3-vs-case_2 were both created, to avoid this case_3 could have been set to: obs, case_1.

**example**
::

    [simulations]
        start_year = 1
        end_year = 2
        [[20180129.DECKv1b_piControl.ne30_oEC.edison]]
            transfer_type = globus
            remote_uuid = 9d6d994a-6d04-11e5-ba46-22000b92c6ec  # required because transfer_type == 'globus'
            remote_path = /global/homes/r/renata/ACME_simulations/20180129.DECKv1b_piControl.ne30_oEC.edison
            short_name = piControl
            native_grid_name = ne30
            native_mpas_grid_name = oEC60to30v3
            data_types = all
            job_types = all
        [[20180215.DECKv1b_1pctCO2.ne30_oEC.edison]]
            transfer_type = sftp
            remote_hostname = edison.nersc.gov                  # required because transfer_type == 'sftp'
            remote_path = /global/homes/r/renata/ACME_simulations/20180215.DECKv1b_1pctCO2.ne30_oEC.edison
            short_name = 1pctCO2
            native_grid_name = ne30
            native_mpas_grid_name = oEC60to30v3
            data_types = all
            job_types = all
        [[20180215.DECKv1b_abrupt4xCO2.ne30_oEC.edison]]
            transfer_type = local           
            local_path = /p/user_pub/e3sm/baldwin32/deck/v1_DECK_abrupt-4xCO2/input # required because transfer_type == 'local'
            short_name = abrupt4xCO2
            native_grid_name = ne30
            native_mpas_grid_name = oEC60to30v3
            data_types = atm, lnd
            job_types = e3sm_diags, amwg, climo
        [[comparisons]]
            20180129.DECKv1b_piControl.ne30_oEC.edison = obs
            20180215.DECKv1b_1pctCO2.ne30_oEC.edison = 20180129.DECKv1b_piControl.ne30_oEC.edison
            20180215.DECKv1b_abrupt4xCO2.ne30_oEC.edison = all


.. _post-processing:

Post processing
---------------

This section of the config is used to configure all post processing jobs. Supported job types are:

    * :ref:`climo`
    * :ref:`timeseries`
    * :ref:`regrid`

.. _climo:

Climo
-----

Produces regridded climatologies using ncclimo. Requires the 'atm' data type. Uses the following config options:

    * run_frequency (list): a space sepperated list of integers. This list will be used to generate the job start/end years. For example if you have 50 years of data you could set the run_frequency = 10, 25, 50 and you would get sets from years 1-10, 11-20, 21-30, 31-40, 41-50, then 1-25, 26-50, and finally 1-50.
    * destination_grid_name (string): the name of the output grid. This can be any string identifier, its just used to group the output.
    * regrid_map_path (string): the path on the local file system to a regrid map suitable for your data and desired output map.

**example**

::

    [post-processing]
        [[climo]]
            run_frequency = 2
            destination_grid_name = fv129x256
            regrid_map_path = /p/cscratch/acme/data/map_ne30np4_to_fv129x256_aave.20150901.nc

.. _timeseries:

Timeseries
----------

Produces single-variable-per-file timeseries files from monthly model output files. Optionally regrids the timeseries output files.

    * run_frequency (list): a space sepperated list of integers. This list will be used to generate the job start/end years. For example if you have 50 years of data you could set the run_frequency = 10, 25, 50 and you would get sets from years 1-10, 11-20, 21-30, 31-40, 41-50, then 1-25, 26-50, and finally 1-50.
    * destination_grid_name (string): the name of the output grid. This can be any string identifier, its just used to group the output.
    * regrid_map_path (string): the path on the local file system to a regrid map suitable for your data and desired output map.
    * atm -> include this key followed by variable names for each atmospheric variable you would like extracted (remote key to turn off atm timeseries generation)
    * lnd -> include this key followed by variable names for each land variable you would like extracted (remote key to turn off lnd timeseries generation)
    * ocn -> include this key followed by variable names for each ocean variable you would like extracted (remote key to turn off ocn timeseries generation)

**example**

::

    [post-processing]
        [[timeseries]]
            run_frequency = 2
            destination_grid_name = fv129x256
            regrid_map_path = /p/cscratch/acme/data/map_ne30np4_to_fv129x256_aave.20150901.nc
            lnd = SOILICE, SOILLIQ, SOILWATER_10CM, QINTR, QOVER, QRUNOFF, QSOIL, QVEGT, TSOI
            atm = FSNTOA, FLUT, FSNT, FLNT, FSNS, FLNS, SHFLX, QFLX, PRECC, PRECL, PRECSC, PRECSL, TS, TREFHT
            ocn = ssh

.. _regrid:

Regrid
------

Translates model output files from one grid into another. Regridding is supported for atm, lnd, and ocn data types. Each regrid type requires its own config section, see example below. To turn off a data type, remove it from the config.

**example**

::

    [post-processing]
        [[regrid]]
            [[[lnd]]]
                source_grid_path = /export/zender1/data/grids/ne30np4_pentagons.091226.nc
                destination_grid_path = /export/zender1/data/grids/129x256_SCRIP.20150901.nc
                destination_grid_name = fv129x256
            [[[atm]]]
                regrid_map_path = /p/cscratch/acme/data/map_ne30np4_to_fv129x256_aave.20150901.nc
                destination_grid_name = fv129x256
            [[[ocn]]]
                regrid_map_path = ~/grids/map_oEC60to30v3_to_0.5x0.5degree_bilinear.nc
                destination_grid_name = 0.5x0.5degree_bilinear

.. _diags:

Diags
-----

This section contains all config options for diagnostic jobs. Currently supported diagnostics are:

    * :ref:`amwg`
    * :ref:`e3sm_diags`
    * :ref:`aprime`

.. _amwg:

AMWG
----

The AMWG diagnostic suite needs the 'atm' data type, and the 'climo' job type.

    * run_frequency (list): a comma sepperated list of integers. This list will be used to generate the job start/end years. For example if you have 50 years of data you could set the run_frequency = 10, 25, 50 and you would get sets from years 1-10, 11-20, 21-30, 31-40, 41-50, then 1-25, 26-50, and finally 1-50.
    * diag_home (string): the path to where on the local file system the amwg code is located. All amwg jobs will be executed from this directory.
    * sets (list): the list of AMWG sets to run, or set to 'all' to run all sets

**example**

::

    [diags]
        [[amwg]]
            run_frequency = 2
            diag_home = /p/cscratch/acme/amwg/amwg_diag
            sets = 2, 3, 4, 4a, 5, 6, 15

.. _e3sm_diags:

e3sm_diags
----------

The e3sm_diags suite needs the 'atm' data type, and the 'climo' job type.

    * run_frequency (list): a comma sepperated list of integers. This list will be used to generate the job start/end years. For example if you have 50 years of data you could set the run_frequency = 10, 25, 50 and you would get sets from years 1-10, 11-20, 21-30, 31-40, 41-50, then 1-25, 26-50, and finally 1-50.
    * backend (string): which graphing backend to use for generating the plots. Supported options are 'vcs' and 'mpl'.
    * reference_data_path (string): path to local copy of reference observational data.

**example**

::

        [diags]
            run_frequency = 2
            backend = vcs
            reference_data_path = /p/cscratch/acme/data/obs_for_acme_diags

.. _aprime:

Aprime
------

The aprime diagnostic suite requires the following data types, and no job types:
    * atm
    * cice
    * cice_restart
    * cice_streams
    * cice_in
    * ocn
    * ocn_restart
    * ocn_streams
    * ocn_in
    * meridionalHeatTransport

To run aprime, your system must have the latest version of the aprime code available. If this is not the case, simple clone the 
`aprime repo <https://github.com/E3SM-Project/a-prime>`_.


**example**

::

        [diags]
            [[aprime]]
                run_frequency = 2
                aprime_code_path = /p/cscratch/acme/data/a-prime

.. _data_types:

Data types
----------

The data_types section is the most complex and configurable part of the run configuration. The basic structure is that each sub-section
defines a type of data, and then gives information about where to find the data, where to store the data, and what the file names are going to be.
The values for each option are templates, which use substitutions to fill out the information at run time. 
Each substitution is made with values specific to the case the data is being included as part of. The following strings are used for replacement:

    * CASEID: the full name for the case.
    * YEAR: the year of the data
    * MONTH: the month for the data
    * LOCAL_PATH: if defined, the local_path specified in the case definition (config.simulation.case)
    * REMOTE_PATH: if defined, the remote_path from the case definition
    * START_YR: the global start_year
    * END_YR: the global end_year
    * REST_YR: the first year that restart data is available, start_year + 1
    * PROJECT_PATH: the global project_path

These are simply the defaults available for all cases, you can define your own substituions on a case-by-case basis by including
the keyword and value in the case definition.


The values for each data type are by default the same for every case, but case specific definitions can be added by creating a new section
inside the data type section with the case name, for example:

::

    [simulations]
        start_year = 1
        end_year = 2
        [[my.case.1]]
            my_custom_keyword = 'isnt-this-nice'
            remote_path = /export/my_user/model_output/my_case
        [[my.case.2]]
            remote_path = /export/my_user/model_output/my_second-case

    [data_types]
        [[some_data_type]]
            remote_path = 'REMOTE_PATH/archive/custom_component/hist'
            file_format = 'CASEID.custom.value.YEAR-MONTH.nc'
            local_path  = '/my/local/path/'
            monthly = True
            [[[my.case.1]]]
                remote_path = 'REMOTE_PATH/MY_CUSTOM_KEYWORD/CASEID'


In the below example, all data types are defined for a case that uses short-term-archiving (note the /archive/atm/hist). The atm and lnd types have been defined for the 20180215.DECKv1b_abrupt4xCO2.ne30_oEC.edison case to NOT use short term archiving. 
For these two data types, the case is expected to use the standard everything-in-the-run-directory method. Note the local_path = 'LOCAL_PATH/atm'

**example**

::

    [data_types]
        [[atm]]
            remote_path = 'REMOTE_PATH/archive/atm/hist'
            file_format = 'CASEID.cam.h0.YEAR-MONTH.nc'
            local_path = 'PROJECT_PATH/input/CASEID/atm'
            monthly = True
            [[[20180215.DECKv1b_abrupt4xCO2.ne30_oEC.edison]]]
                local_path = 'LOCAL_PATH/atm'
        [[lnd]]
            remote_path = 'REMOTE_PATH/archive/lnd/hist'
            file_format = 'CASEID.clm2.h0.YEAR-MONTH.nc'
            local_path = 'PROJECT_PATH/input/CASEID/lnd'
            monthly = True
            [[[20180215.DECKv1b_abrupt4xCO2.ne30_oEC.edison]]]
                local_path = 'LOCAL_PATH/lnd'
        [[cice]]
            remote_path = 'REMOTE_PATH/archive/ice/hist'
            file_format = 'mpascice.hist.am.timeSeriesStatsMonthly.YEAR-MONTH-01.nc'
            local_path = 'PROJECT_PATH/input/CASEID/ice'
            monthly = True
        [[ocn]]
            remote_path = 'REMOTE_PATH/archive/ocn/hist'
            file_format = 'mpaso.hist.am.timeSeriesStatsMonthly.YEAR-MONTH-01.nc'
            local_path = 'PROJECT_PATH/input/CASEID/ocn'
            monthly = True
        [[ocn_restart]]
            remote_path = 'REMOTE_PATH/archive/rest/REST_YR-01-01-00000/'
            file_format = 'mpaso.rst.REST_YR-01-01_00000.nc'
            local_path = 'PROJECT_PATH/input/CASEID/rest'
            monthly = False
        [[cice_restart]]
            remote_path = 'REMOTE_PATH/archive/rest/REST_YR-01-01-00000/'
            file_format = 'mpascice.rst.REST_YR-01-01_00000.nc'
            local_path = 'PROJECT_PATH/input/CASEID/rest'
            monthly = False
        [[ocn_streams]]
            remote_path = 'REMOTE_PATH/run'
            file_format = 'streams.ocean'
            local_path = 'PROJECT_PATH/input/CASEID/mpas'
            monthly = False
        [[cice_streams]]
            remote_path = 'REMOTE_PATH/run'
            file_format = 'streams.cice'
            local_path = 'PROJECT_PATH/input/CASEID/mpas'
            monthly = False
        [[ocn_in]]
            remote_path = 'REMOTE_PATH/run'
            file_format = 'mpas-o_in'
            local_path = 'PROJECT_PATH/input/CASEID/mpas'
            monthly = False
        [[cice_in]]
            remote_path = 'REMOTE_PATH/run'
            file_format = 'mpas-cice_in'
            local_path = 'PROJECT_PATH/input/CASEID/mpas'
            monthly = False
        [[meridionalHeatTransport]]
            remote_path = 'REMOTE_PATH/archive/ocn/hist'
            file_format = 'mpaso.hist.am.meridionalHeatTransport.START_YR-02-01.nc'
            local_path = 'PROJECT_PATH/input/CASEID/mpas'
            monthly = False


.. _example_config:

Example Configuration
---------------------

This is an example configuration used on acme1 with three cases. Each case uses a different transfer method.

::

    [global]
    project_path = /p/user_pub/e3sm/baldwin32/model_v_model
    email = baldwin32@llnl.gov
    native_grid_cleanup = False
    local_globus_uuid = a871c6de-2acd-11e7-bc7c-22000b9a448b

    [img_hosting]
        img_host_server = acme-viewer.llnl.gov
        host_directory = /var/www/acme/acme-diags/baldwin32/
        url_prefix = 'baldwin32'

    [simulations]
        start_year = 1
        end_year = 2
        [[20180129.DECKv1b_piControl.ne30_oEC.edison]]
            transfer_type = globus
            remote_uuid = 9d6d994a-6d04-11e5-ba46-22000b92c6ec
            remote_path = /global/homes/r/renata/ACME_simulations/20180129.DECKv1b_piControl.ne30_oEC.edison
            short_name = piControl
            native_grid_name = ne30
            native_mpas_grid_name = oEC60to30v3
            data_types = all
            job_types = all
        [[20180215.DECKv1b_1pctCO2.ne30_oEC.edison]]
            transfer_type = sftp
            remote_hostname = edison.nersc.gov
            remote_path = /global/homes/r/renata/ACME_simulations/20180215.DECKv1b_1pctCO2.ne30_oEC.edison
            short_name = 1pctCO2
            native_grid_name = ne30
            native_mpas_grid_name = oEC60to30v3
            data_types = all
            job_types = all
        [[20180215.DECKv1b_abrupt4xCO2.ne30_oEC.edison]]
            transfer_type = local
            local_path = /p/user_pub/e3sm/baldwin32/deck/v1_DECK_abrupt-4xCO2/input
            short_name = abrupt4xCO2
            native_grid_name = ne30
            native_mpas_grid_name = oEC60to30v3
            data_types = atm, lnd
            job_types = e3sm_diags, amwg, climo
        [[comparisons]]
            20180129.DECKv1b_piControl.ne30_oEC.edison = obs
            20180215.DECKv1b_1pctCO2.ne30_oEC.edison = 20180129.DECKv1b_piControl.ne30_oEC.edison
            20180215.DECKv1b_abrupt4xCO2.ne30_oEC.edison = all

    [post-processing]
        [[climo]]
            run_frequency = 2
            destination_grid_name = fv129x256
            regrid_map_path = /p/cscratch/acme/data/map_ne30np4_to_fv129x256_aave.20150901.nc

        [[timeseries]]
            run_frequency = 2
            destination_grid_name = fv129x256
            regrid_map_path = /p/cscratch/acme/data/map_ne30np4_to_fv129x256_aave.20150901.nc
            atm = FSNTOA, FLUT, FSNT, FLNT, FSNS, FLNS, SHFLX, QFLX, PRECC, PRECL, PRECSC, PRECSL, TS, TREFHT
            lnd = SOILICE, SOILLIQ, SOILWATER_10CM, QINTR, QOVER, QRUNOFF, QSOIL, QVEGT, TSOI

        [[regrid]]
            [[[lnd]]]
                source_grid_path = /export/zender1/data/grids/ne30np4_pentagons.091226.nc
                destination_grid_path = /export/zender1/data/grids/129x256_SCRIP.20150901.nc 
                destination_grid_name = fv129x256
            [[[atm]]]
                regrid_map_path = /p/cscratch/acme/data/map_ne30np4_to_fv129x256_aave.20150901.nc
                destination_grid_name = fv129x256
            [[[ocn]]]
                regrid_map_path = ~/grids/map_oEC60to30v3_to_0.5x0.5degree_bilinear.nc
                destination_grid_name = 0.5x0.5degree_bilinear


    [diags]
        [[e3sm_diags]]
            run_frequency = 2
            backend = mpl
            reference_data_path = /p/cscratch/acme/data/obs_for_acme_diags

        [[amwg]]
            run_frequency = 2
            diag_home = /p/cscratch/acme/amwg/amwg_diag
            sets = all

        [[aprime]]
            run_frequency = 2
            host_directory = aprime-diags
            aprime_code_path = /p/cscratch/acme/data/a-prime

    [data_types]
        [[atm]]
            remote_path = 'REMOTE_PATH/archive/atm/hist'
            file_format = 'CASEID.cam.h0.YEAR-MONTH.nc'
            local_path = 'PROJECT_PATH/input/CASEID/atm'
            monthly = True
            [[[20180215.DECKv1b_abrupt4xCO2.ne30_oEC.edison]]]
                local_path = 'LOCAL_PATH/atm'
        [[lnd]]
            remote_path = 'REMOTE_PATH/archive/lnd/hist'
            file_format = 'CASEID.clm2.h0.YEAR-MONTH.nc'
            local_path = 'PROJECT_PATH/input/CASEID/lnd'
            monthly = True
            [[[20180215.DECKv1b_abrupt4xCO2.ne30_oEC.edison]]]
                local_path = 'LOCAL_PATH/lnd'
        [[cice]]
            remote_path = 'REMOTE_PATH/archive/ice/hist'
            file_format = 'mpascice.hist.am.timeSeriesStatsMonthly.YEAR-MONTH-01.nc'
            local_path = 'PROJECT_PATH/input/CASEID/ice'
            monthly = True
        [[ocn]]
            remote_path = 'REMOTE_PATH/archive/ocn/hist'
            file_format = 'mpaso.hist.am.timeSeriesStatsMonthly.YEAR-MONTH-01.nc'
            local_path = 'PROJECT_PATH/input/CASEID/ocn'
            monthly = True
        [[ocn_restart]]
            remote_path = 'REMOTE_PATH/archive/rest/REST_YR-01-01-00000/'
            file_format = 'mpaso.rst.REST_YR-01-01_00000.nc'
            local_path = 'PROJECT_PATH/input/CASEID/rest'
            monthly = False
        [[cice_restart]]
            remote_path = 'REMOTE_PATH/archive/rest/REST_YR-01-01-00000/'
            file_format = 'mpascice.rst.REST_YR-01-01_00000.nc'
            local_path = 'PROJECT_PATH/input/CASEID/rest'
            monthly = False
        [[ocn_streams]]
            remote_path = 'REMOTE_PATH/run'
            file_format = 'streams.ocean'
            local_path = 'PROJECT_PATH/input/CASEID/mpas'
            monthly = False
        [[cice_streams]]
            remote_path = 'REMOTE_PATH/run'
            file_format = 'streams.cice'
            local_path = 'PROJECT_PATH/input/CASEID/mpas'
            monthly = False
        [[ocn_in]]
            remote_path = 'REMOTE_PATH/run'
            file_format = 'mpas-o_in'
            local_path = 'PROJECT_PATH/input/CASEID/mpas'
            monthly = False
        [[cice_in]]
            remote_path = 'REMOTE_PATH/run'
            file_format = 'mpas-cice_in'
            local_path = 'PROJECT_PATH/input/CASEID/mpas'
            monthly = False
        [[meridionalHeatTransport]]
            remote_path = 'REMOTE_PATH/archive/ocn/hist'
            file_format = 'mpaso.hist.am.meridionalHeatTransport.START_YR-02-01.nc'
            local_path = 'PROJECT_PATH/input/CASEID/mpas'
            monthly = False
    