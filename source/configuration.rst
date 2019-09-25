.. _configuration:

*****************
Run Configuration
*****************

See `here for real life configuration examples <https://github.com/E3SM-Project/processflow/tree/master/samples>`_

For an example config with all the available options turned on
see the :ref:`example_config`


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

**example**
::

    [global]
        project_path = /p/user_pub/e3sm/baldwin32/deck/bcrc_spinup  # base path for the project
        email = baldwin32@llnl.gov                                  # my email address so I can get notifications

.. _img_hosting:

img_hosting
-----------

This is an optional section, only needed if the user would like to turn on web hosting for diagnostic plot output. To turn off output hosting, simply remove this section from the configuration.

    * img_host_server (string): The base url of the webserver, used for constructing the notification email links.
    * host_directory (string): The base directory for where to put output for web hosting, the user must have permission to write here. Directories will be created for each simulation case, with jobs for the case stored below it.
    * url_prefix (string): Notification urls are constructed as: ``https://{img_host_server}/{url_prefix}/{case}/{diagnostic}`` the url_prefix is used if the hosting service uses a specific string for your host directory.

**example**
::

    [img_hosting]
        img_host_server = acme-viewer.llnl.gov                  # this hypothetical run is happen on acme1.llnl.gov, see :ref:`machine_sp`
        host_directory = /var/www/acme/acme-diags/baldwin32
        url_prefix = baldwin32

.. _simulations:

simulations
-----------

This section is used for configuring each case. As many cases can be placed here as the user would like (one or more). 
The cases can be very different from each other, use different naming conventions (see data_types), and have their data stored in different file structures. 
The one thing they must all share in common is the start_year and end_year attributes.

    * start_year (int): the first year of data to be used.
    * end_year (int): the last year of data.

**A new section is created for each case, allowing very different configs for the different cases.**

    * [[CASEID]] (string): this should be the full case name e.g. [[20180129.DECKv1b_piControl.ne30_oEC.edison]]
    * short_name (string): a nice short name for the case, this can be any string identifier for this case
    * native_grid_name (string): the name of the native grid used in the land and atmospheric components
    * native_mpas_grid_name (string): the name of the mpas grid
    * data_types (list): which data types should be copied for this case, this must include all data_types needed for jobs this case will be running in a space seperated list. Can be set to 'all' to mean all data types described in the data_types section.
    * job_types (list): which of the job types should be run on this case. Use the keyword 'all' to run all defined jobs on this case.


**If running diagnostic jobs, the comparisons key must be included**

This is the list of comparisons between for each case.
Each case running diagnostics should have an entry here, followed by
which other cases it should be compared to. This can include the keywords
'all' for all possible comparisons, or 'obs' for model-vs-obs comparisons.
The 'all' keyword will add comparisons with each other case as well as
model-vs-obs.


::

    comparisons = obs, case_2
        or
    comparisons = case_3
        or
    comparisons = all

In this example the following comparison diagnostics jobs will be generated:

    * case_1-vs-obs, case_1-vs-case_2
    * case_2-vs-case_3
    * case_3-vs-case_1, case_3-vs-case_2, case_3-vs-obs

Note how case_2-vs-case_3 and case_3-vs-case_2 were both created,
to avoid this case_3 could have been set to: obs, case_1.

**example**
::

    [simulations]
        start_year = 1
        end_year = 2
        [[20180129.DECKv1b_piControl.ne30_oEC.edison]]
            short_name = piControl
            native_grid_name = ne30
            native_mpas_grid_name = oEC60to30v3
            data_types = all
            job_types = all
            comparisons = obs
        [[20180215.DECKv1b_1pctCO2.ne30_oEC.edison]]
            short_name = 1pctCO2
            native_grid_name = ne30
            native_mpas_grid_name = oEC60to30v3
            data_types = all
            job_types = all
            comparisons = 20180129.DECKv1b_piControl.ne30_oEC.edison
        [[20180215.DECKv1b_abrupt4xCO2.ne30_oEC.edison]]
            short_name = abrupt4xCO2
            native_grid_name = ne30
            native_mpas_grid_name = oEC60to30v3
            data_types = atm, lnd
            job_types = e3sm_diags, amwg, climo
            comparisons = all

.. _post-processing:

Post processing
---------------

This section of the config is used to configure all post processing jobs.
Supported job types are:

    * :ref:`climo`
    * :ref:`timeseries`
    * :ref:`regrid`

.. _climo:

Climo
-----

Produces regridded climatologies using ncclimo. Requires the 'atm' data type.
Uses the following config options:

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
            [[[custom_args]]] # OPTIONAL SLURM ARGUMENTS
                --partition = regular
                --account = e3sm

.. _timeseries:

Timeseries
----------

Produces single-variable-per-file timeseries files from monthly model
output files. Optionally regrids the timeseries output files.

    * run_frequency (int list): a space sepperated list of integers. This list will be used to generate the job start/end years. For example if you have 50 years of data you could set the run_frequency = 10, 25, 50 and you would get sets from years 1-10, 11-20, 21-30, 31-40, 41-50, then 1-25, 26-50, and finally 1-50.
    * destination_grid_name (string): the name of the output grid. This can be any string identifier, its just used to group the output.
    * regrid_map_path (string): the path on the local file system to a regrid map suitable for your data and desired output map.
    * atm (string list): include this key followed by variable names for each atmospheric variable you would like extracted (remote key to turn off atm timeseries generation)
    * lnd (string list): include this key followed by variable names for each land variable you would like extracted (remote key to turn off lnd timeseries generation)
    * ocn (string list): include this key followed by variable names for each ocean variable you would like extracted (remote key to turn off ocn timeseries generation)

**example**

::

    [post-processing]
        [[timeseries]]
            run_frequency = 2
            destination_grid_name = fv129x256
            regrid_map_path = /p/cscratch/acme/data/map_ne30np4_to_fv129x256_aave.20150901.nc
            lnd = SOILICE, SOILLIQ, SOILWATER_10CM, QINTR, QOVER, QRUNOFF, QSOIL, QVEGT, TSOI
            atm = FSNTOA, FLUT, FSNT, FLNT, FSNS, FLNS, SHFLX, QFLX, PRECC, PRECL, PRECSC, PRECSL, TS, TREFHT
            [[[custom_args]]] # OPTIONAL SLURM ARGUMENTS
                --partition = regular
                --account = e3sm

.. _regrid:

Regrid
------

Translates model output files from one grid into another. Regridding
is supported for atm, lnd, and ocn data types. Each regrid type requires
its own config section, see example below. To turn off a data type, remove
it from the config.

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
            [[[custom_args]]] # OPTIONAL SLURM ARGUMENTS
                --partition = regular
                --account = e3sm

.. _diags:

Diags
-----

This section contains all config options for diagnostic jobs. Currently
supported diagnostics are:

    * :ref:`amwg`
    * :ref:`e3sm_diags`
    * :ref:`aprime`
    * :ref:`mpas-analysis`

.. _amwg:

AMWG
----

The AMWG diagnostic suite needs the 'atm' data type, and is dependent on
the 'climo' job type.

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
            [[[custom_args]]] # OPTIONAL SLURM ARGUMENTS
                --partition = regular
                --account = e3sm

.. _e3sm_diags:

e3sm_diags
----------

The e3sm_diags suite needs the 'atm' data type, and is dependent on the
'climo' job type.

    * run_frequency (list): a comma sepperated list of integers. This list will be used to generate the job start/end years. For example if you have 50 years of data you could set the run_frequency = 10, 25, 50 and you would get sets from years 1-10, 11-20, 21-30, 31-40, 41-50, then 1-25, 26-50, and finally 1-50.
    * backend (string): which graphing backend to use for generating the plots. Supported options are 'vcs' and 'mpl'.
    * reference_data_path (string): path to local copy of reference observational data.

**example**

::

        [diags]
            [[e3sm_diags]]
                run_frequency = 2
                backend = mpl
                reference_data_path = /p/cscratch/acme/data/obs_for_acme_diags
                [[[custom_args]]] # OPTIONAL SLURM ARGUMENTS
                    --partition = regular
                    --account = e3sm

.. _aprime:

Aprime
------

The aprime diagnostic suite requires the following data types, and is not
dependent on any other job types:

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

To run aprime, your system must have the latest version of the aprime code
available. If this is not the case, simply clone the
`aprime repo <https://github.com/E3SM-Project/a-prime>`_.


**example**

::

        [diags]
            [[aprime]]
                run_frequency = 2
                aprime_code_path = /p/cscratch/acme/data/a-prime
                [[[custom_args]]] # OPTIONAL SLURM ARGUMENTS
                    --partition = regular
                    --account = e3sm

.. _mpas-analysis:

MPAS-Analysis
-------------

For the complete mpas-analysis documentation see the MPAS_Documentation_

.. _MPAS_Documentation: https://mpas-analysis.readthedocs.io/en/master/

The MPAS-Analysis diagnostic suite requires the following data types:

    * cice
    * cice_restart
    * cice_streams
    * cice_in
    * ocn
    * ocn_restart
    * ocn_streams
    * ocn_in
    * meridionalHeatTransport

The mpas-analysis job has the following config keys:

    * mapping_directory: this is the path to the directory containing map files.
    * generate_plots: a list of plots to generate
    * start_year_offset, optional: the time series start offset
    * ocn_obs_data_path, optional: if the ocean observations are stored in a custom location
    * seaice_obs_data_path, optional: if the seaice observations are stored in a custom location
    * region_mask_path, optional: if the region masks are stored in a custom location
    * ocean_namelist_name: the filename of the ocean namelist file, typically mpas-o_in or mpaso_in
    * seaice_namelist_name: the filename of the seaice namelist file, typically mpas-cice_in or mpassi_in

**example**

::

    [[mpas_analysis]]
        mapping_directory = /space2/diagnostics/mpas_analysis/maps
        generate_plots = 'all', 'no_landIceCavities', 'no_eke', 'no_BGC', 'no_icebergs', 'no_min', 'no_max'
        start_year_offset = True
        ocn_obs_data_path = /space2/diagnostics/observations/Ocean/
        seaice_obs_data_path = /space2/diagnostics/observations/SeaIce/
        region_mask_path = /space2/diagnostics/mpas_analysis/region_masks
        ocean_namelist_name = mpaso_in
        seaice_namelist_name = mpassi_in



.. _data_types:

Data types
----------

The data_types section is the most complex and configurable part of
the configuration process. The basic structure is that each sub-section
defines a type of data, and then gives information about where to find
the data, where to store the data, and what the file names are going to be.
The values for each option are templates, which use substitutions to fill
out the information at run time. Each substitution is made with values
specific to the case the data is being included as part of. The
following strings are used for replacement:

    * CASEID: the full name for the case.
    * YEAR: the year of the data
    * MONTH: the month for the data
    * LOCAL_PATH: if defined for the case, the local_path specified in the case definition (config.simulation.case)
    * REMOTE_PATH: if defined for the case, the remote_path from the case definition
    * START_YR: the global start_year
    * END_YR: the global end_year
    * REST_YR: the first year that restart data is available, start_year + 1
    * PROJECT_PATH: the global project_path

These are simply the defaults available for all cases, you can define
your own substituions on a case-by-case basis by including the keyword
and value in the case definition.


The values for each data type are by default the same for every case,
but case specific definitions can be added by creating a new section
inside the data type section with the case name. In this example, the
my.case.1 remote_path option over rides the default value, and includes
a custom substitution keyword. Note that the keyword when defined must
be lower case, but when used in the data_type value must be upper case.

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


In the below example, all data types are defined for a case that
uses short-term-archiving (note the /archive/atm/hist). The atm and lnd
types have been defined for the 20180215.DECKv1b_abrupt4xCO2.ne30_oEC.edison
case to NOT use short term archiving. For these two data types, the case
is expected to use the standard everything-in-the-run-directory method.
Note the local_path = 'LOCAL_PATH/atm'

**example**

::

    [data_types]
        [[atm]]
            file_format = CASEID.cam.h0.YEAR-MONTH.nc
            local_path = PROJECT_PATH/input/CASEID/atm
            monthly = True
            [[[20180215.DECKv1b_abrupt4xCO2.ne30_oEC.edison]]]
                local_path = LOCAL_PATH/atm
        [[lnd]]
            file_format = CASEID.clm2.h0.YEAR-MONTH.nc
            local_path = PROJECT_PATH/input/CASEID/lnd
            monthly = True
            [[[20180215.DECKv1b_abrupt4xCO2.ne30_oEC.edison]]]
                local_path = LOCAL_PATH/lnd
        [[cice]]
            file_format = mpascice.hist.am.timeSeriesStatsMonthly.YEAR-MONTH-01.nc
            local_path = PROJECT_PATH/input/CASEID/ice
            monthly = True
        [[ocn]]
            file_format = mpaso.hist.am.timeSeriesStatsMonthly.YEAR-MONTH-01.nc
            local_path = PROJECT_PATH/input/CASEID/ocn
            monthly = True
        [[ocn_restart]]
            file_format = mpaso.rst.REST_YR-01-01_00000.nc
            local_path = PROJECT_PATH/input/CASEID/rest
            monthly = False
        [[cice_restart]]
            file_format = mpascice.rst.REST_YR-01-01_00000.nc
            local_path = PROJECT_PATH/input/CASEID/rest
            monthly = False
        [[ocn_streams]]
            file_format = streams.ocean
            local_path = PROJECT_PATH/input/CASEID/mpas
            monthly = False
        [[cice_streams]]
            file_format = streams.cice
            local_path = PROJECT_PATH/input/CASEID/mpas
            monthly = False
        [[ocn_in]]
            file_format = mpas-o_in
            local_path = PROJECT_PATH/input/CASEID/mpas
            monthly = False
        [[cice_in]]
            file_format = mpas-cice_in
            local_path = PROJECT_PATH/input/CASEID/mpas
            monthly = False
        [[meridionalHeatTransport]]
            file_format = mpaso.hist.am.meridionalHeatTransport.START_YR-02-01.nc
            local_path = PROJECT_PATH/input/CASEID/mpas
            monthly = False
