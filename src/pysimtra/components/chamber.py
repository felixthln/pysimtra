from pathlib import Path
import numpy as np


class Chamber:

    """
    Class for describing a SIMTRA sputter chamber.
    """

    # Chamber parameters
    shape: str = None  # either "cuboid" or "cylinder"
    length: float = None  # length of the chamber in m
    radius: float = None  # radius in m, only used when shape = "cylinder"
    height: float = None  # height in m, only used when shape = "cuboid"
    width: float = None  # width in m, only used when shape = "cuboid"
    temperature: float = None  # in Kelvin
    pressure: float = None  # in Pa
    gas_element: str = None  # noble gas
    seed_number: int = None
    chamber_walls_grid: tuple = None  # (N_x, N_y, N_z, N_theta), x, y, z for shape = "cuboid", z, theta for "cylinder"
    save_deposition_walls: list[int] = None
    save_individual_data: bool = None

    def __init__(self, shape: str, length: float, temperature: float, pressure: float, gas_element: str,
                 radius: float = None, height: float = None, width: float = None, seed_number: int = None,
                 chamber_walls_grid: tuple = (10, 10, 10, 180), save_deposition_walls: list[int] = None,
                 save_individual_data: bool = False):

        """
        :param shape: shape of the chamber, either "cuboid" or "cylinder"
        :param length: length of the chamber in m (z-direction)
        :param temperature: temperature of the chamber in K
        :param pressure: pressure of the chamber in Pa
        :param gas_element: gas element of the chamber, only noble gases
        :param radius: radius of the chamber in m, only needed when chamber is a cylinder
        :param height: height of the chamber in m (x-direction), only needed when chamber is a cuboid
        :param width: width of the chamber in m (y-direction), only needed when chamber is a cuboid
        :param seed_number: number defining the random state of SIMTRA. By default, a random number will be chosen
        :param chamber_walls_grid:
        :param save_deposition_walls:
        :param save_individual_data:
        """

        # Check if a valid element was entered and throw an error if not
        if gas_element not in ['He', 'Ne', 'Ar', 'Kr', 'Xe', 'Rn']:
            raise ValueError('The selected gas element is not a noble gas.')
        # Store the parameters
        self.shape = shape
        self.radius = radius
        self.height = height
        self.width = width
        self.length = length
        self.temperature = temperature
        self.pressure = pressure
        self.gas_element = gas_element
        # Set the seed number
        self.set_seed_number(seed_number)
        # Set the default values for the deposition parameters if not defined
        self.chamber_walls_grid = chamber_walls_grid
        self.save_deposition_walls = [] if save_deposition_walls is None else save_deposition_walls
        self.save_individual_data = save_individual_data

    @classmethod
    def cylindrical(cls, radius: float, length: float, temperature: float = 293.15, pressure: float = 1.0,
                    gas_element: str = 'Ar', seed_number: int = None):

        """
        Creates a cylindrical sputter chamber from a given radius and height.

        :param radius: radius of the cylinder in meters
        :param length: length of the cylinder in meters
        :param temperature: temperature of the gas in Kelvin, default is 283.15 K
        :param pressure: pressure of the gas in Pa, default is 1 Pa
        :param gas_element: sputter gas, defaults to Ar
        :param seed_number: number defining the random state of Simtra. By default, a random number will be chosen.
        """

        # Create the class from the given parameters
        return cls('cylinder', length, temperature, pressure, gas_element, radius=radius, seed_number=seed_number)

    @classmethod
    def rectangular(cls, height: float, width: float, length: float, temperature: float = 293.15, pressure: float = 1.0,
                    gas_element: str = 'Ar', seed_number: int = None):

        """
        Creates a cylindrical sputtering chamber from a given radius and height.

        :param height: height of the rectangle (in x direction) in meters
        :param width: width of the rectangle (in y direction) in meters
        :param length: length of the rectangle (in z direction) in meters
        :param temperature: temperature of the gas in Kelvin, default is 283.15 K
        :param pressure: pressure of the gas in Pa, default is 1 Pa
        :param gas_element: sputter gas given by the standard periodic table symbol or name, defaults to Ar
        :param seed_number: number defining the random state of Simtra. By default, a random number will be chosen.
        :return: Chamber object
        """

        # Create the class from the given parameters
        return cls('cuboid', length, temperature, pressure, gas_element, height=height, width=width,
                   seed_number=seed_number)

    @classmethod
    def from_file(cls, path: Path | str):

        """
        Creates a Chamber object from a given ".sin" file. Only the top section "chamber" of the file will be
        parsed.

        :param path: path to the simtra input file with ending ".sin"
        :return: Chamber object
        """

        # Import the method here to avoid circular imports
        from ..simtra_read import read_sin
        # Convert the string to a path if necessary
        path = Path(path) if isinstance(path, str) else path
        # Only ".sin" (text) files are supported here
        if path.suffix == '.sin':
            # Create the class from the file
            return read_sin(path, only_chamber=True)
        # Raise an error for the wrong file type
        else:
            raise ValueError('The given path needs to point to a ".sin" file.')

    def set_seed_number(self, seed: int = None):

        """
        Sets the seed number of the class either randomly or to the specified number.

        :param seed: seed number between 1 and 10000
        """

        self.seed_number = np.random.randint(1, 10000) if seed is None else seed

    def __eq__(self, other) -> bool:

        # Check if the second object is a Chamber too
        if isinstance(other, Chamber):
            # Check if the parameters of both classes are identical
            return vars(self) == vars(other)
        # In any other case, return an error
        return NotImplemented
