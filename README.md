# pySIMTRA

`pySIMTRA` is a Python wrapper for `SIMTRA` (<ins>Si</ins>mulation of <ins>M</ins>etal <ins>Tra</ins>nsport), a Monte 
Carlo code for simulating the transport of sputtered atoms through the gas phase<sup>1,2</sup>. SIMTRA allows for the 
definition of custom sputter systems in 3D by a graphical user interface and does not only calculate the deposition 
profile, but also properties of the deposited atoms such as energy and direction. pySIMTRA extends this functionality by 
allowing to define custom systems programmatically via code but most importantly enables the simulation of co-sputtering
experiments through the parallel execution of the SIMTRA simulations with multithreading.

The package is part of a scientific publication *A Python-Based Approach to Sputter Deposition Simulations in 
Combinatorial Materials Science* which can be found here:

> Arxiv: https://doi.org/10.48550/arXiv.2411.14413

References:

<sup>1</sup> van Aeken, K., Mahieu, S., & Depla, D. (2008). The metal flux from a rotating cylindrical magnetron: a 
Monte Carlo simulation. Journal of Physics D: Applied Physics, 41(20), 205307.

<sup>2</sup> Depla, D., & Leroy, W. P. (2012). Magnetron sputter deposition as visualized by Monte Carlo modeling. Thin 
Solid Films, 520(20), 6337–6354.

## Installation & Documentation

The package is on pip and can be easily installed via `pip install pysimtra`. More detailed instructions in how to 
install the package, user guides and an API reference can be found on 
[ReadTheDocs](https://pysimtra.readthedocs.io/en/latest/index.html).

## Terms of Use

The package is distributed under the [GNU GPLv3](https://www.gnu.org/licenses/quick-guide-gplv3.html) license. See the 
[LICENSE](LICENSE) for details. It was developed by Felix Thelen.

## Contributing

If you have suggestions how to make the package better in any way or want to contribute to the code yourself, please 
write an Email to [Felix Thelen](felix.thelen@ruhr-uni-bochum.de). We are open for feedback!
