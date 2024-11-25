from .surface import Surface


class Cylinder(Surface):

    """
    Class for describing a SIMTRA cylinder.
    """

    # Internal SIMTRA representation
    simtra_type: str = 'cylinderpiece'
    # Specific parameters of the cylinder
    radius: float = None  # in m
    height: float = None  # in m
    dtheta: float = None  # in °

    def __init__(self, name: str, radius: float, height: float, position: tuple = (0, 0, 0),
                 orientation: tuple = (0, 0, 0), dtheta: float = 180, save_avg_data: bool = False,
                 save_ind_data: bool = False, avg_grid: tuple[int] = None):

        """
        :param name: name of the cylinder
        :param radius: radius of the circle in m
        :param height: height of the rectangle in m
        :param position: position (x, y, z) in m
        :param orientation: orientation (phi, theta, psi) in °
        :param dtheta: opening angle of the cylinder in °, defaults to a full cylinder
        :param save_avg_data: whether the average data should be saved, defaults to False
        :param save_ind_data: whether the individual data should be saved, defaults to False
        :param avg_grid: averaging grid size, tuple with number of segments in x and y direction. Ignored if
            save_avg_data is False
        """

        # Initialize the superclass
        super().__init__(name, position, orientation, save_avg_data, save_ind_data, avg_grid)
        # Store the specific parameters inside the class
        self.radius = radius
        self.height = height
        self.dtheta = dtheta
