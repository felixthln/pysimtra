from .surface import Surface


class Cone(Surface):

    """
    Class for describing a SIMTRA cone.
    """

    def __init__(self, name: str, small_rho: float, big_rho: float, height: float, position: tuple = (0, 0, 0),
                 orientation: tuple = (0, 0, 0), dtheta: float = 180, save_avg_data: bool = False,
                 save_ind_data: bool = False, avg_grid: tuple[int, int] = None):

        """
        :param name: name of the cone
        :param small_rho: small radius of the cone in m
        :param big_rho: big radius of the cone in m
        :param height: height of the cone in m
        :param position: position (x, y, z) in m
        :param orientation: orientation (phi, theta, psi) in °
        :param dtheta: opening angle of the cone in °, defaults to a full cone
        :param save_avg_data: whether the average data should be saved, defaults to False
        :param save_ind_data: whether the individual data should be saved, defaults to False
        :param avg_grid: averaging grid size, tuple with the number of segments along the circumference (theta) and
            along z², i.e. the second one bins the square of the height coordinate and not the height itself. A single
            number is used for both directions, no grid averages over the whole cone. Ignored if save_avg_data is
            False
        """

        # Initialize the superclass
        super().__init__(name, position, orientation, save_avg_data, save_ind_data, avg_grid)
        # Internal SIMTRA representation
        self.simtra_type: str = 'conepiece'

        # Store the specific parameters inside the class
        self.small_rho: float = small_rho  # in m
        self.big_rho: float = big_rho  # in m
        self.height: float = height  # in m
        self.dtheta: float = dtheta  # in °
