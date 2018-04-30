.. _configuration:

*************
Configuration
*************

This guide goes through each one of the options in the run configuration file.

Project Path
------------
The project_path is the root directory for your processflow run on your local machine. All the input and output is stored by default under this directory. This can be a new directory, or one that already exists.
If you like, you can pre-stage your data (for example if your machine doesnt have a globus node) under <project_path>/input/<data_type>

Source Path
-----------
The source_path is the location of your data on the remote machine. This is the path on the remote machine that created the model output. If running from local pre-staged data, this key is ignored.

Short Term Archive
------------------
This should be turned on (1) if the remote data source has had short term archiving run on the model data. Otherwise turn off (0).

Simulation Start Year
---------------------
The simulation_start_year is the first year of data to move and process. This doesnt have to be the first year of model data produced, it just has to be any number between 1 and the last year of data.

Simulation End Year
-------------------
The simulation_start_year key is the last year of model data to process. It doesnt have to be the last year of produced data, and can be any positive number. If the model is still running 
and the simulation_end_year is larger then the latest year produced, the processflow will wait as the data is generated and run jobs once the data is ready.

Experiment
----------
The experiment key is the name of the experiment and is used to find all the input data files. This should be the prefix to the model output files, e.g. if your datafiles are named
"20171122.beta3rc10_1850.ne30_oECv3_ICG.edison.cam.h0.0100-12.nc," the experiment would be "20171122.beta3rc10_1850.ne30_oECv3_ICG.edison."

Short name
----------
A short name for the experiment that will be used in the AMWG and E3SM diags plots.

Set Frequency
-------------
The set_frequency are the year lengths that the jobs will be run on. This can be one number or a list of numbers, for example set_frequency = 5, 20 would setup jobs to run
every 5 years as well as every 20 years.

Email
-----
The email address to send notifications to when all processing is complete, leave commented out to turn off.

Native Grid Cleanup
-------------------
If turned on (1) the native_grid_cleanup option will cause native grid climatology files to be discarded after a successful run. To keep the native grid files, turn the option off (0).

Native Grid Name
----------------
The native_grid_name should be the name of the native grid, but can be any name for the directory that holds native grid files. 

Remap Grid Name
---------------
The remap_grid_name should be the name of the remapped grid, but can be any name for the directory that holds the regridded file.

Img Host Server
---------------
The url prefix for the server that will be hosting the diagnostic plots, e.g. https://acme-viewer.llnl.gov for acme1.llnl.gov.

Host Directory
--------------
The path the processflow should copy diagnostic plots to so they can be hosted. This is whatever directory apache has been configured to host files from.

File Types
----------
The file_types is a list of file types that are required to run the jobs. If running with only AMWG or E3SM, only atm files are required. All others are needed for aprime diags.
Accepted file types are: 'atm', 'ice', 'ocn', 'rest', 'streams.ocean', 'streams.cice', 'mpas-o_in', 'mpas-cice_in', 'meridionalHeatTransport', 'lnd'. Data types map to the following directories

├── atm
│   └── CASE_ID.cam.h0.YYYY-MM.nc
├── ice
│   └── mpascice.hist.am.timeSeriesStatsMonthly.YYYY-MM-DD.nc
├── lnd
│   └── CASE_ID.clm2.h0.YYYY-MM.nc
├── mpas
│   ├── mpas-cice_in
│   ├── mpaso.hist.am.meridionalHeatTransport.YYYY-MM-DD.nc
│   ├── mpas-o_in
│   ├── streams.cice
│   └── streams.ocean
├── ocn
│   └── mpaso.hist.am.timeSeriesStatsMonthly.YYYY-MM-DD.nc
└── rest
    ├── mpascice.rst.YYYY-MM-DD_00000.nc
    └── mpaso.rst.YYYY-MM-DD_00000.nc


Set Jobs
--------
The set_jobs section is where you configure which jobs will be run on which year sets. For each job, list which year sets you would like it to be run on.
For example if you had used the set_frequency key to create 5 and 20 year sets, and you wanted all the diagnostics run on the 20 years, but only e3sm_diags on the 5 years
then you could use the following:

.. code-block:: python

    [[set_jobs]]
    ncclimo = 5, 20
    timeseries = 20
    amwg = 20
    aprime_diags = 20
    e3sm_diags = 5


E3SM Diags
----------
Each of the jobs has their own configuration options. The E3SM options available are:
    * host_directory: the name that should be used when hosting this job. e.g. e3sm_diags
    * backend: the plotting backend, either vcs or mpl
    * seasons: Which seasoms to run on (any or all) DJF, MAM, JJA, SON, ANN
    * reference_data_path: the path to reference data, e.g. /p/cscratch/acme/data/obs_for_acme_diags
    * sets: which plot sets should be produced (any or all) 3, 4, 5, 7, 13

Transfer
--------
    * destination_endpoint: The globus endpoint ID of the local machine (the transfer destination when moving from the remote server).
    * source_endpoint: The Globus endpoint ID for the remote host

AMWG
----
    * diag_home: The code path to where amwg is installed.
    * host_directory: the directory name to use when hosting the amwg output. e.g. amwg

Ncclimo
-------
    * regrid_map_path: The path to the regrid map. On acme1 the ne30 to fv129x256 map is located at /p/cscratch/acme/data/map_ne30np4_to_fv129x256_aave.20150901.nc
    * var_list: This is a list of variables to extract as time series files when running the timeseries job.

APrime Diags
------------
    * host_directory: the directory name to use when hosting the amwg output. e.g. aprime
    * aprime_code_path: the path to where the aprime repository has been cloned. On acme1 it can be found at /p/cscratch/acme/data/a-prime
    * test_atm_res: The native atm grid name
    * test_mpas_mesh_name: The native mpas grid name