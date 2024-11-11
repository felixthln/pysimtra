# pySIMTRA

`pySIMTRA` is a Python wrapper for `SIMTRA` (<ins>Si</ins>mulation of <ins>M</ins>etal <ins>Tra</ins>nsport), a Monte 
Carlo code for simulating the transport of sputtered atoms through the gas phase<sup>1,2</sup>.`SIMTRA` allows for the 
definition of custom sputter systems in 3D by a graphical user interface and does not only calculate the deposition 
profile, but also properties of the deposited atoms such as energy and direction. pySIMTRA extends this functionality by 
allowing to define custom systems programmatically via code but most importantly enables the simulation of co-sputtering
experiments through the parallel execution of the SIMTRA simulations with multithreading. 

In order to use this wrapper, the SIMTRA application needs to be acquired first from 
[here](https://www.ugent.be/we/solidstatesciences/draft/en/services/software). Since SIMTRA only runs on Windows 
operating systems, the part of the package running the actual simulation can only be used on Windows. However, defining, 
loading and exporting components and sputter systems also works on the other operating systems.

<sup>1</sup> van Aeken, K., Mahieu, S., & Depla, D. (2008). The metal flux from a rotating cylindrical magnetron: a 
Monte Carlo simulation. Journal of Physics D: Applied Physics, 41(20), 205307.

<sup>2</sup> Depla, D., & Leroy, W. P. (2012). Magnetron sputter deposition as visualized by Monte Carlo modeling. Thin 
Solid Films, 520(20), 6337–6354.

## Getting started

The code was developed on Python 3.11. Since the code is not yet on pip, the quickest way to get started is to clone 
this repository. Run the following command in the command line

```
git clone https://github.com/felixthln/pysimtra.git
cd pysimtra
```

...and install it with pip:

```
pip install .
```

Before starting a simulation, the method following method needs to be called once in order to assign the SIMTRA 
executable to the package. For this, first import the installed package into your code.

```
import pysimtra as ps

# Specify the path to the directory with the SIMTRA executables
simtra_path = 'add-your-path-here'
# Import the executables into the package
ps.import_exe(simtra_path)
```

Afterward, all functionalities of the package can be used to full extend. The main capabilities are shown in the 
jupyter notebook [examples.ipynb](examples.ipynb).

## Limitations

Still needs to be defined. For example, the functionality for the SIMTRA movement features are not implemented (yet)

## Terms of Use

The package is distributed under the [GNU GPLv3](https://www.gnu.org/licenses/quick-guide-gplv3.html) license. See the 
[LICENSE](LICENSE) for details. It was developed by Felix Thelen.

## Contributing

If you have suggestions how to make the package better in any way or want to contribute to the code yourself, please 
write an Email to [Felix Thelen](felix.thelen@ruhr-uni-bochum.de). We are open for feedback!
