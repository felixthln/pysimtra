from .surface import Surface


class Sphere(Surface):

    """
    Class for describing a SIMTRA sphere.
    """

    def __init__(self, name: str, radius: float, dphi: float = 180, position: tuple = (0, 0, 0),
                 orientation: tuple = (0, 0, 0), dtheta: float = 180, save_avg_data: bool = False,
                 save_ind_data: bool = False, avg_grid: tuple[int, int] = None):

        """
        :param name: name of the sphere
        :param radius: radius of the sphere in m
        :param dphi: opening angle of the sphere along phi in °, defaults to a full sphere. SIMTRA writes it as the
            second of the two angles
        :param position: position (x, y, z) in m
        :param orientation: orientation (phi, theta, psi) in °
        :param dtheta: opening angle of the sphere along theta in °, defaults to a full sphere. SIMTRA writes it as
            the first of the two angles
        :param save_avg_data: whether the average data should be saved, defaults to False
        :param save_ind_data: whether the individual data should be saved, defaults to False
        :param avg_grid: averaging grid size, tuple with the number of segments along cos(theta) and along phi, i.e.
            the first one bins the cosine of the polar angle and not the angle itself. A single number is used for
            both directions, no grid averages over the whole sphere. Ignored if save_avg_data is False
        """

        # Initialize the superclass
        super().__init__(name, position, orientation, save_avg_data, save_ind_data, avg_grid)
        # Internal SIMTRA representation
        self.simtra_type: str = 'spherepiece'
        # Store the specific parameters inside the class
        self.radius = radius  # in m
        self.dphi = dphi  # in °
        self.dtheta = dtheta  # in °
