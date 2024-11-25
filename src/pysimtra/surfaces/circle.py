from .plane import Plane


class Circle(Plane):

    def __init__(self, name: str, radius: float, position: tuple = (0, 0, 0), orientation: tuple = (0, 0, 0),
                 dtheta: float = 180, save_avg_data: bool = False, save_ind_data: bool = False,
                 avg_grid: tuple[int, ...] = None):
        """
        :param name: name of the circle
        :param radius: radius of the circle in m
        :param position: position (x, y, z) in m
        :param orientation: orientation (phi, theta, psi) in °
        :param dtheta: opening angle of the circle in °, defaults to a full circle
        :param save_avg_data: whether the average data should be saved, defaults to False
        :param save_ind_data: whether the individual data should be saved, defaults to False
        :param avg_grid: averaging grid size, tuple with number of segments in x and y direction
        :return: Circle object
        """

        # Initialize the parent class
        super().__init__(name, 'circle', position=position, orientation=orientation, radius=radius, dtheta=dtheta,
                         save_avg_data=save_avg_data, save_ind_data=save_ind_data, avg_grid=avg_grid)
