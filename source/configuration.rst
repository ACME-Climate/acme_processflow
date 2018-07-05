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

.. _global_config:

global
------

The global section has the following keys: 
    * project_path: This is the base of the project directory tree. All input and output will be stored here under /input/ and /output/
    * email: This is an email address to send notification emails to
    * native_grid_cleanup: This is a boolean flag to denoting if the native grid files produced by post processing jobs should be deleted after all jobs successfully complete
    * local_globus_uuid: The local globus transfer nodes unique id. This is optional and only required if using globus for file transfers

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

This is an optional section, only needed if the user would like to turn on web hosting for diagnostic plot output. To turn this off, simply remove this section from the configuration.
    * img_host_server: The base url of the webserver, used for constructing the notification email links.
    * host_directory: The base directory for where to put output for web hosting, the user must have write permission here. Directories will be created for each simulation case, with jobs for the case stored below it.
    * url_prefix: Notification urls are constructed as https://{img_host_server}/{url_prefix}/{case}/{diagnostic}

**example**
::

        [img_hosting]
            img_host_server = your-web-server.institution.domain
            host_directory = /path/to/where/you/host/your/files/
            url_prefix = /any/prefix/you/need/

.. _simulations:

simulations
-----------

This section is used for configuring each case. As many cases can be placed here as the user would like. 
The cases can be very different from each other, use different naming conventions (see data_types), and have their data stored in different file structures. 
The one thing they must all share in common is the start_year and end_year.

    * start_year: the first year of data to be used. For example, if start_year is set to 5, then files with years >= 5 && <= end_year will be concidered as part of the data set.
    * end_year: the last year of data. For example if end_year is 10, then files with years >= start_year && <= 10 will be concidered as part of the dataset.

**Each case must exist in its own config section, denoted by [[CASEID]] the double brackets are important.**

    * [[CASEID]] this should be the full case name e.g. [[20180129.DECKv1b_piControl.ne30_oEC.edison]]
    * short_name: a nice short name for the case, this can be any string identifier for this case
    * native_grid_name: the name of the native grid used in the land and atmospheric components
    * native_mpas_grid_name: the name of the mpas grid
    * data_types: which data types should be copied for this case, this must include all data_types needed for jobs this case will be running. Can be set to 'all' to mean all data types described in the data_types section
    * job_types: which of the job types should be run on this case. Use the keyword 'all' to run all defined jobs on this case.

**If running diagnostic jobs, the following section must be included: [[comparisons]]**
    
This is the list of comparisons between for each case. 
Each case running diagnostics should have an entry here, followed by which other cases it should be compared to. 
This can include the keywords 'all' for all possible comparisons, or 'obs' for model-vs-obs comparisons. The 'all' keyword will add comparisons with each other case as well as model-vs-obs.
    
example:
    * case_1: obs , case_2
    * case_2: case_3
    * case_3: all

In this example the following comparison diagnostics jobs will be generated:
    * case_1-vs-obs, case_1-vs-case_2
    * case_2-vs-case_3
    * case_3-vs-case_1, case_3-vs-case_2, case_3-vs-obs

Note how case_2-vs-case_3 and case_3-vs-case_2 were both created, to avoid this case_3 could have been set to: obs, case_1.


**transfer_type**
Each simulated case needs to have a transfer type. Transfer_type can be one of three different values, which force certain values to be included for the case:

    * 'local' --> the case must then also have 'local_path,' which is then used to specify the location for each datatype in the data_types section
    * 'sftp' --> the case must then also have 'remote_hostname,' which is the remote server to connect to and 'remote_path'
    * 'globus' --> the case must then also have 'remote_uuid,' which is the globus unique identifier for the remote node, and 'remote_path'. The 'global' section should also include the 'local_globus_uuid' key.

**example**
::

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

Produces regridded climatologies using ncclimo. Requires the 'atm' data type.

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

**example**

::

        [post-processing]
            [[timeseries]]
                run_frequency = 2
                destination_grid_name = fv129x256
                regrid_map_path = /p/cscratch/acme/data/map_ne30np4_to_fv129x256_aave.20150901.nc
                lnd = SOILICE, SOILLIQ, SOILWATER_10CM, QINTR, QOVER, QRUNOFF, QSOIL, QVEGT, TSOI
                atm = FSNTOA, FLUT, FSNT, FLNT, FSNS, FLNS, SHFLX, QFLX, PRECC, PRECL, PRECSC, PRECSL, TS, TREFHT

.. _regrid:

Regrid
------

Translates model output files from one grid into another.

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

The AMWG diagnostic suite needs the 'atm' data type, and the 'climo' job type

**example**

::

    [diags]
        [[amwg]]
            run_frequency = 2
            diag_home = /p/cscratch/acme/amwg/amwg_diag

.. _e3sm_diags:

e3sm_diags
----------

The e3sm_diags suite needs the 'atm' data type, and the 'climo' job type.

**example**

::

        [diags]
            run_frequency = 2
            backend = mpl
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

**example**

::

        [diags]
            [[aprime]]
                run_frequency = 2
                aprime_code_path = /p/cscratch/acme/data/a-prime

.. _data_types:

Data types
----------

This section defines each of the data types for your jobs. Each data type is denoted by creating a new config section using double brackets [[new_data_type]].
Each section then has four keys. The values in these keys can contain a set of keywords that are used to substitute values at run time. For example, the REMOTE_PATH keyword
pulls in remote_path from the simulation config and substitures it. For example, a new data type could be specified using:

::

        [simulations]
            start_year = 22
            end_year = 44
            [[some-case-id]]
                remote_path = /export/my_user/model-output/my-case

        [data_types]
            [[my_new_custom_type]]
                remote_path = 'REMOTE_PATH/archive/custom_component/hist'
                file_format = 'CASEID.custom.value.YEAR-MONTH.nc'
                local_path = '/my/custom/local/path/'
                monthly = True

This would create a new data type called "my_new_custom_type." The processflow would then take the cases "remote_path" and replace the REMOTE_PATH section defined in the data_type, making it look for this new data type in
/export/my_user/model-output/my-case/archive/custom_component/hist, with the file names some-case-id.custom.value.0022-01.nc through some-case-id.custom.value.0044-12.nc

The keywords you can use for substitution are:
    * REMOTE_PATH: pulled from the simulation.case.remote_path
    * PROJECT_PATH: pulled from global.project_path
    * CASEID: pulled from simulations.case
    * YEAR: created as a range from simulation.start_year to simulation.end_year if the data_type is marked as monthly
    * MONTH: created as a range from 1 to 12 if the data_type is marked as monthly
    * REST_YR: this is the "restart year," which is simulations.start_year + 1

The four mandatory sections for each data type (remote_path, file_format, local_path, monthly) are applied to each case. Case specific options are allowed, and allow you to create user defined substutions.
Simply add the caseid as a new section to the data_type section, and add your case specific keywords. These values for these keywords are then pulled from the simulation.caseid section. For example:

::

    [simulations]
        start_year = 1
        end_year = 2
        [[my-fancy-case]]
            my_custom_keyword = 'isnt-this-nice'
            remote_path = /export/my_user/model-output/my-case
        [[perfectly-ordinary-case]]
            remote_path = /export/my_user/model-output/my-second-case

    [data_types]
        [[my_new_custom_type]]
            remote_path = 'REMOTE_PATH/archive/custom_component/hist'
            file_format = 'CASEID.custom.value.YEAR-MONTH.nc'
            local_path = '/my/custom/local/path/'
            monthly = True
            [[[my-fancy-case]]]
                remote_path = 'REMOTE_PATH/MY_CUSTOM_KEYWORD/CASEID'

In this example the data type my_new_custom_type would specify that files coming from the case my-fancy-case would have the remote path:

| {remote_path from simulation.caseid}/{my_custom_keyword}/{ case id}
| /export/my_user/model-output/my-case/isnt-this-nice/my-fancy-case



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