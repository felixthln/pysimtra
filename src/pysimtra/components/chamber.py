from pathlib import Path
import numpy as np


class Chamber:

    """
    Class for describing a SIMTRA sputter chamber.
    """

    def __init__(self, shape: str, length: float, temperature: float, pressure: float, gas_element: str,
                 radius: float = None, height: float = None, width: float = None, seed_number: int = None,
                 avg_grid: tuple[int, ...] = (10, 10, 10, 180), save_avg_data: bool = False,
                 save_ind_data: bool = False):

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
        :param avg_grid: grid used for averaging the particles deposited on the chamber walls. For a cuboid, it holds
            the number of bins along x, y and z, for a cylinder an additional number of angular bins, i.e.
            (N_x, N_y, N_z, N_theta). Shorter tuples are accepted, see "normalize_avg_grid". The grid is only used if
            save_avg_data is True, but SIMTRA always stores it, defaulting to (10, 10, 10, 180)
        :param save_avg_data: whether the averaged data of the particles deposited on the chamber walls should be
            saved, defaults to False. Either all walls are saved or none of them, see "save_deposition_walls"
        :param save_ind_data: whether the individual data of the particles deposited on the chamber walls should be
            saved, defaults to False
        """

        # Check if a valid element was entered and throw an error if not
        if gas_element not in ['He', 'Ne', 'Ar', 'Kr', 'Xe', 'Rn']:
            raise ValueError('The selected gas element is not a noble gas.')
        # Store the parameters
        self.shape = shape  # either "cuboid" or "cylinder"
        self.radius = radius  # radius in m, only used when shape = "cylinder"
        self.height = height  # height in m, only used when shape = "cuboid"
        self.width = width  # width in m, only used when shape = "cuboid"
        self.length = length  # length of the chamber in m
        self.temperature = temperature  # in Kelvin
        self.pressure = pressure  # in Pa
        self.gas_element = gas_element  # noble gas
        # Set the seed number
        self.set_seed_number(seed_number)
        # Particle saving preferences of the chamber walls. The grid is brought into the form expected for the given
        # chamber shape, since that is the form SIMTRA writes it in
        self.avg_grid: tuple[int, ...] = self.normalize_avg_grid(shape, avg_grid)
        self.save_avg_data: bool = save_avg_data
        self.save_ind_data: bool = save_ind_data

    @staticmethod
    def normalize_avg_grid(shape: str, avg_grid: tuple[int, ...]) -> tuple[int, ...]:

        """
        Brings an averaging grid of the chamber walls into the form SIMTRA expects for a given chamber shape, which is
        (N_x, N_y, N_z) for a cuboid and (N_x, N_y, N_z, N_theta) for a cylinder. As a convenience, the linear bin
        numbers may also be given as a single number which is then used for all three axes, i.e. (N, N_theta) or (N,)
        which is what the SIMTRA user interface does for a cylinder. For a cylinder, the number of angular bins may be
        omitted, in which case it defaults to 180.

        :param shape: shape of the chamber, either "cuboid" or "cylinder"
        :param avg_grid: averaging grid of the chamber walls
        :return: averaging grid with one entry per number SIMTRA writes into the input file
        """

        # Convert all entries to integers since they are bin numbers
        grid = tuple(int(n) for n in avg_grid)
        # A grid without bins is not a valid input for SIMTRA
        if any(n < 1 for n in grid):
            raise ValueError('All bin numbers of the averaging grid need to be larger than zero.')
        # A cuboid has one bin number per axis, each of its six walls uses the two fitting ones
        if shape == 'cuboid':
            # Use the same number of bins along all three axes
            if len(grid) == 1:
                grid = grid * 3
            # Drop the number of angular bins, which is only used by a cylinder
            elif len(grid) == 4:
                grid = grid[:3]
            # Any other length cannot be mapped onto the three axes
            if len(grid) != 3:
                raise ValueError('The averaging grid of a cuboid chamber needs to hold three bin numbers '
                                 '(N_x, N_y, N_z), got %d.' % len(grid))
        # A cylinder has an additional number of angular bins used by its lateral surface
        elif shape == 'cylinder':
            # Use the same number of bins along all three axes and keep the angular one
            if len(grid) == 2:
                grid = grid[:1] * 3 + grid[1:]
            # Fall back to the SIMTRA default of 180 angular bins
            elif len(grid) == 3:
                grid = grid + (180,)
            # Any other length cannot be mapped onto the three axes and the angle
            if len(grid) != 4:
                raise ValueError('The averaging grid of a cylindrical chamber needs to hold four bin numbers '
                                 '(N_x, N_y, N_z, N_theta), got %d.' % len(grid))
        # Only the two shapes above are known to SIMTRA
        else:
            raise ValueError('The chamber shape needs to be either "cuboid" or "cylinder", got "%s".' % shape)
        # Return the normalized grid
        return grid

    @property
    def save_deposition_walls(self) -> list[int]:

        """
        Returns the 1-based indices of the chamber walls whose averaged deposition data SIMTRA saves. The indices
        cannot be chosen freely: either the data of all walls is saved or of none of them, which is why they only
        depend on the chamber shape, a cuboid having six walls and a cylinder three.

        :return: list of the wall indices, empty if save_avg_data is False
        """

        # Without averaging, SIMTRA leaves the list of walls empty
        if not self.save_avg_data:
            return []
        # A cylinder consists of the lateral surface and its two end caps, a cuboid of six faces
        return [1, 2, 3] if self.shape == 'cylinder' else [1, 2, 3, 4, 5, 6]

    @classmethod
    def cylindrical(cls, radius: float, length: float, temperature: float = 293.15, pressure: float = 1.0,
                    gas_element: str = 'Ar', seed_number: int = None, avg_grid: tuple[int, ...] = (10, 10, 10, 180),
                    save_avg_data: bool = False, save_ind_data: bool = False):

        """
        Creates a cylindrical sputter chamber from a given radius and height.

        :param radius: radius of the cylinder in meters
        :param length: length of the cylinder in meters
        :param temperature: temperature of the gas in Kelvin, default is 283.15 K
        :param pressure: pressure of the gas in Pa, default is 1 Pa
        :param gas_element: sputter gas, defaults to Ar
        :param seed_number: number defining the random state of Simtra. By default, a random number will be chosen.
        :param avg_grid: averaging grid of the chamber walls, either (N_x, N_y, N_z, N_theta) or (N, N_theta) to use
            the same number of bins along all three axes. Defaults to (10, 10, 10, 180)
        :param save_avg_data: whether the averaged data of the particles deposited on the chamber walls should be
            saved, defaults to False
        :param save_ind_data: whether the individual data of the particles deposited on the chamber walls should be
            saved, defaults to False
        """

        # Create the class from the given parameters
        return cls('cylinder', length, temperature, pressure, gas_element, radius=radius, seed_number=seed_number,
                   avg_grid=avg_grid, save_avg_data=save_avg_data, save_ind_data=save_ind_data)

    @classmethod
    def rectangular(cls, height: float, width: float, length: float, temperature: float = 293.15, pressure: float = 1.0,
                    gas_element: str = 'Ar', seed_number: int = None, avg_grid: tuple[int, ...] = (10, 10, 10),
                    save_avg_data: bool = False, save_ind_data: bool = False):

        """
        Creates a cylindrical sputtering chamber from a given radius and height.

        :param height: height of the rectangle (in x direction) in meters
        :param width: width of the rectangle (in y direction) in meters
        :param length: length of the rectangle (in z direction) in meters
        :param temperature: temperature of the gas in Kelvin, default is 283.15 K
        :param pressure: pressure of the gas in Pa, default is 1 Pa
        :param gas_element: sputter gas given by the standard periodic table symbol or name, defaults to Ar
        :param seed_number: number defining the random state of Simtra. By default, a random number will be chosen.
        :param avg_grid: averaging grid of the chamber walls, either (N_x, N_y, N_z) or a single number to use the
            same number of bins along all three axes. Defaults to (10, 10, 10)
        :param save_avg_data: whether the averaged data of the particles deposited on the chamber walls should be
            saved, defaults to False
        :param save_ind_data: whether the individual data of the particles deposited on the chamber walls should be
            saved, defaults to False
        :return: Chamber object
        """

        # Create the class from the given parameters
        return cls('cuboid', length, temperature, pressure, gas_element, height=height, width=width,
                   seed_number=seed_number, avg_grid=avg_grid, save_avg_data=save_avg_data,
                   save_ind_data=save_ind_data)

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
