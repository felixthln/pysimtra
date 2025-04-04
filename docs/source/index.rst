########
pySIMTRA
########

``pySIMTRA`` is a Python wrapper for `SIMTRA <https://www.ugent.be/we/solidstatesciences/draft/en/services/software>`_
(**Si**\ mulation of **M**\ etal **Tra**\ nsport), a Monte Carlo code for simulating the transport
of sputtered atoms through the gas phase. SIMTRA allows for the definition of custom sputter systems in 3D by a
graphical user interface and does not only calculate the deposition profile, but also properties of the deposited atoms
such as energy and direction. pySIMTRA extends this functionality by allowing to define custom systems
programmatically via code but most importantly enables the simulation of co-sputtering experiments through the parallel
execution of the SIMTRA simulations with multithreading.

The package is part of a scientific publication *A Python-Based Approach to Sputter Deposition Simulations in
Combinatorial Materials Science* which can be found here:

    Surface and Coatings Technology: https://doi.org/10.1016/j.surfcoat.2025.131998

Documentation
-------------

If you're new to pySIMTRA we suggest you to start with:

.. toctree::
   :maxdepth: 2

   getting_started/index

For examples in how to define custom sputter systems see:

.. toctree::
   :maxdepth: 2

   user_guide/index

For a description of all provided classes and methods see:

.. toctree::
   :maxdepth: 2

   api_reference/index
