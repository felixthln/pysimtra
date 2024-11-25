from .surface import Surface


class Sphere(Surface):

    """
    Class for describing a SIMTRA sphere.
    """

    # Internal SIMTRA representation
    simtra_type: str = 'spherepiece'
    # Specific parameters of the sphere
    radius: float = None  # in m
    dphi: float = None  # in °
    dtheta: float = None  # in °

    def __init__(self, name: str, radius: float, dphi: float = 180, position: tuple = (0, 0, 0),
                 orientation: tuple = (0, 0, 0), dtheta: float = 180, save_avg_data: bool = False,
                 save_ind_data: bool = False, avg_grid: tuple[int, ...] = None):

        """
        :param name: name of the sphere
        :param radius: radius of the sphere in m
        :param dphi: opening angle 1 of the sphere in °, defaults to a sphere
        :param position: position (x, y, z) in m
        :param orientation: orientation (phi, theta, psi) in °
        :param dtheta: opening angle 2 of the sphere in °, defaults to a full sphere
        :param save_avg_data: whether the average data should be saved, defaults to False
        :param save_ind_data: whether the individual data should be saved, defaults to False
        :param avg_grid: averaging grid size, tuple with number of segments in x and y direction. Ignored if
            save_avg_data is False
        """

        # Initialize the superclass
        super().__init__(name, position, orientation, save_avg_data, save_ind_data, avg_grid)
        # Store the specific parameters inside the class
        self.radius = radius
        self.dphi = dphi
        self.dtheta = dtheta
