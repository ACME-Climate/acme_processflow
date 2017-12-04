******************
A-Prime Diagnostic
******************

`A-Prime <https://github.com/ACME-Climate/a-prime>`_ runs a subset of atmospheric plots, as well
as the MPAS ocean analysis including ENSO diagnostics.

Configuration
-------------

The A-Prime diagnostics required significantly more data then other diagnostic packages.

*NOTE:* A-Prime will only run on the following machines due to hardcoded hostnames: edison, rhea/titan, acme1, aims4, wolf. If running on another machine/facility, simply remove aprime from the job_sets in your config file.

.. code-block:: python

    [global]
    ...
    set_frequency = SOME_LENGTH

    file_types = 'atm', 'ice', 'ocn', 'rest', 'streams.ocean', 'streams.cice', 'mpas-o_in', 'mpas-cice_in', 'meridionalHeatTransport'
    
    [[set_jobs]]
        aprime = SOME_LENGTH
    
    [aprime_diags]
    # The directory to copy plots for hosting
    host_directory = aprime-diags

    # The code directory for aprime
    aprime_code_path = /p/cscratch/acme/data/a-prime

    # the atmospheric reslution of your simulation
    test_atm_res = ne30
    # the mpas mesh name used
    test_mpas_mesh_name = oEC60to30v3

Dependencies
------------

For the MPAS analysis to run, A-Prime needs atmospheric as well as all the MPAS ocean files. Because it computes its own climatologies it does
not require ncclimo to run first.
