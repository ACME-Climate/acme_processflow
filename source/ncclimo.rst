******************
Ncclimo Diagnostic
******************

`Ncclimo <https://www.mankier.com/1/ncclimo>`_ takes raw model data and produces regridded climatologies, as well as
extracting time series variables.

Configuration
-------------

.. code-block:: python

    [global]
    ...
    set_frequency = <some_length>

    file_types = 'atm'
    ...
    
    [[set_jobs]]
        ncclimo = <some_length>
    
    [ncclimo]
    # Path to the regird map
    regrid_map_path = /p/cscratch/acme/data/map_ne30np4_to_fv129x256_aave.20150901.nc

    # A list of variables to generate timeseries files for
    var_list = FSNTOA, FLUT, FSNT, FLNT, FSNS, FLNS, SHFLX, QFLX, PRECC, PRECL, PRECSC, PRECSL, TS, TREFHT

Dependencies
------------

The only dependency for ncclimo is that in the file_types list the "atm" key is set. Ncclimo will then
generate regridded climatologies to be used by diagnostic packages.
