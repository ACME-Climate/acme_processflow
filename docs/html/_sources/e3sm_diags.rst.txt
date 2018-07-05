***************
ACME Diagnostic
***************

The `E3SM Diags <https://github.com/ACME-Climate/acme_diags>`_ is the Diagnostic
ploting software made at LLNL to modernize many of the features of AMWG.

These are the relavent configuration options for e3sm_diags. 
Configuration
-------------

.. code-block:: python

    [global]
    ...
    set_frequency = <some_length>
    ...
    file_types = 'atm'
    ...

    [[set_jobs]]
        ncclimo = <some_length>
        e3sm_diags = <some_length>
    
    [e3sm_diags]
    # The directory to copy output to for web hosting
    # This path is relative to the global host_prefix
    host_directory = e3sm-diags

    # ACME diags can use several backends to generate plots, currently matplotlib (mpl) and vcs (vcs) are supported.
    backend = vcs

    # seasons list to generate plots for 
    seasons = DJF, MAM, JJA, SON, ANN

    # path to observation data
    reference_data_path = /p/cscratch/acme/data/obs_for_acme_diags

    # list of diagnostic sets to run
    sets = 3, 4, 5, 7, 13

Dependencies
------------

The ACME diagnostic is very similar to AMWG but more modern. It has the same data requirement that ncclimo produce regridded climatologies. As such, for each year_set that e3sm_diags runs, ncclimo must also run.

