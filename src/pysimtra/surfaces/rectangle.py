from .plane import Plane


class Rectangle(Plane):

    def __init__(self, name: str, dx: float, dy: float, position: tuple = (0, 0, 0), orientation: tuple = (0, 0, 0),
                 save_avg_data: bool = False, save_ind_data: bool = False, avg_grid: tuple[int, ...] = None):

        """
        :param name: name of the rectangle
        :param dx: half width of the rectangle in m
        :param dy: half height of the rectangle in m
        :param position: position (x, y, z) in m
        :param orientation: orientation (phi, theta, psi) in °
        :param save_avg_data: whether the average data should be saved, defaults to False
        :param save_ind_data: whether the individual data should be saved, defaults to False
        :param avg_grid: averaging grid size, tuple with number of segments in x and y direction
        :return: Rectangle object
        """

        # Initialize the parent class
        super().__init__(name, 'rectangle', dx=dx, dy=dy, position=position, orientation=orientation,
                         save_avg_data=save_avg_data, save_ind_data=save_ind_data, avg_grid=avg_grid)
