Installation
============

This section goes through the required steps to get ``pySIMTRA`` running on your system.

Acquire the SIMTRA application
------------------------------

Since this package is based on SIMTRA, the **application needs to be acquired first** (for free) from
`here <https://www.ugent.be/we/solidstatesciences/draft/en/services/software>`_. Since SIMTRA only runs on Windows
operating systems, the part of the package running the actual simulation **can only be used on Windows**. However,
defining, loading and exporting components and sputter systems also works on the other operating systems.

Install the package via pip
---------------------------

The code was developed on Python 3.11. If you want to test the package in a separated environment and you are using
`Anaconda <https://www.anaconda.com>`_, we recommend to create a new conda environment first via the following command:

.. code-block::

   conda create -n pysimtra_env python=3.11

Since the code is not yet on pip, the quickest way to get started is to clone the GitHub repository. However, the
installation requirements were already defined. Therefor, the package can be automatically installed via pip locally.
Run the following command in the command line to clone the repository:

.. code-block::

   git clone https://github.com/felixthln/pysimtra.git
   cd pysimtra

...and install it with pip:

.. code-block::

   pip install .

Import the SIMTRA application into the package
----------------------------------------------

Lastly, the acquired SIMTRA application needs to be imported into ``pySIMTRA`` so it can be automatically accessed when
executing simulations. For this, first import the installed package into your code, then define the path of the
directory containing the SIMTRA application (the ".exe" files and other downloaded folders). Finally, run the method
``ps.import_exe`` in order to import the application. The import is permanent, therefor this only needs to be done once
or after updating the package.

.. code-block::

   import pysimtra as ps

   # Specify the path to the directory with the SIMTRA executables
   simtra_path = 'add-your-path-here'
   # Import the executables into the package
   ps.import_exe(simtra_path)

Afterward, all functionalities of the package can be used to full extend. Visit the
:doc:`User Guide <../user_guide/index>` to learn the basic functionalities based on examples. The full API is
specified in the :doc:`API Reference <../api_reference/index>` section.
