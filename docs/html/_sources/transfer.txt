***************
Globus Transfer
***************

`Globus <https://www.globus.org/>`_ is a tool for the bulk site to site transfer or large datasets.

Configuration
-------------

You will need to find the globus node UUIDs for your source and destination nodes. They can be found by logging into Globus `here <https://www.globus.org/app/login>`_,
navigating to Endpoints in the upper right, searching for the DTN and looking for its UUID in the node attributes.

.. code-block:: python

    [global]
    ...
    # The directory to store model output on the local machine
    project_path = /p/cscratch/acme/USER_NAME/PROJECT/input

    # This is the remote path to the run directory for your experiment. For example if your simulation was run on edison
    # the path would look something like 
    # /scratch2/scratchdirs/golaz/ACME_simulations/20170313.beta1_02.A_WCYCL1850S.ne30_oECv3_ICG.edison
    source_path = /SOME/PATH/TO/AN/EXPERIMENT/
    
    [transfer]
    # The Globus endpoint ID for the local host
    destination_endpoint = a871c6de-2acd-11e7-bc7c-22000b9a448b

    # The Globus endpoint ID for the remote host
    source_endpoint = b9d02196-6d04-11e5-ba46-22000b92c6ec

Dependencies
------------

The data transfer job is the base job that starts all runs (unless you already have your data local). The acme_processflow will automatically 
generate transfer jobs dynamically as the monitor detects files on the remote host. This means you can start the acme_processflow at the same
time you start the simulation, and it will wait for data to be generated and transfer it as it is created.

Once you start your run, if the source and destination nodes have not been activated with your credentials you will be prometed to
log into Globus and activate the nodes. If you're running in headless mode, you will be sent an email with activation links, and the workflow
will pause until you finish the activation process.