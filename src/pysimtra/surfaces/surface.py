

class Surface:

    """
    Base class for all SIMTRA surfaces.
    """

    def __init__(self, name: str, position: tuple = (0, 0, 0), orientation: tuple = (0, 0, 0),
                 save_avg_data: bool = False, save_ind_data: bool = False, avg_grid: tuple[int, int] | int | None = None):

        """
        Base class of all SIMTRA surfaces, holding the properties every surface has. It is not meant to be used
        directly, use one of the subclasses instead.

        :param name: name of the surface
        :param position: position (x, y, z) in m, relative to the object the surface belongs to
        :param orientation: orientation (phi, theta, psi) in °, relative to the object the surface belongs to
        :param save_avg_data: whether the data of the particles deposited on the surface should be saved averaged
            over the cells of the averaging grid, defaults to False
        :param save_ind_data: whether the data of every individual particle deposited on the surface should be saved,
            defaults to False
        :param avg_grid: averaging grid size, tuple with the number of segments along the two directions of the
            surface. Which directions these are depends on the surface type, see the subclasses. A single number is
            used for both directions, no grid averages over the whole surface. Ignored if save_avg_data is False
        """

        # Internal SIMTRA representation
        self.simtra_type: str = None
        # Store the properties inside the class
        self.name: str = name  # Name of the surface
        # Position and orientation of the surface
        self.position: tuple = position  # (x, y, z) in m
        self.orientation: tuple = orientation  # (phi, theta, psi) in °
        # Particle saving preferences
        self.save_avg_data: bool = save_avg_data
        self.save_ind_data: bool = save_ind_data
        # The averaging grid always holds two bin numbers, whose meaning depends on the surface type
        self.avg_grid: tuple[int, int] = self.normalize_avg_grid(avg_grid)
        # Quantities SIMTRA averages over the grid, which are written behind the bin numbers. The user interface
        # always writes these three, but whatever a file holds is kept so that it survives a read and write cycle
        self.avg_quantities: tuple[str, ...] = ('N', 'E', 'NColl')

    @staticmethod
    def normalize_avg_grid(avg_grid: tuple[int, int] | int | None) -> tuple[int, int]:

        """
        Brings an averaging grid into the form SIMTRA expects, which is two bin numbers. As a convenience, a single
        number may be given, which is then used for both directions. If no grid is given at all, a single bin is used,
        i.e. the quantities are averaged over the whole surface.

        :param avg_grid: averaging grid of the surface, either as a tuple of two bin numbers or as a single number
        :return: averaging grid as a tuple of two bin numbers
        """

        # Without a grid, SIMTRA still needs two bin numbers, a single bin averaging over the whole surface
        if avg_grid is None:
            return (1, 1)
        # Accept a single number, which is then used along both directions
        grid = tuple(avg_grid) if hasattr(avg_grid, '__iter__') else (avg_grid,)
        # Convert all entries to integers since they are bin numbers
        grid = tuple(int(n) for n in grid)
        # Use the same number of bins along both directions
        if len(grid) == 1:
            grid = grid * 2
        # Any other length cannot be mapped onto the two directions of the grid
        if len(grid) != 2:
            raise ValueError('The averaging grid of a surface needs to hold two bin numbers, got %d.' % len(grid))
        # A grid without bins is not a valid input for SIMTRA
        if any(n < 1 for n in grid):
            raise ValueError('All bin numbers of the averaging grid need to be larger than zero.')
        # Return the normalized grid
        return grid
