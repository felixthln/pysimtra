from .surface import Surface


class Plane(Surface):

    """
    Class for describing a SIMTRA plane, which can either be a circle, rectangle or perforated representations of
    those.
    """

    # Internal SIMTRA representation
    simtra_type: str = 'planepiece'
    # Type specifying whether the plane is a circle or rectangle
    plane_type: str = None  # either "circle" or "rectangle"
    perforation_type: str = None  # either "circle" or "rectangle"
    # Inner and outer parameters of the planepiece
    outer_param_1: float = None  # either radius (m) or width (m)
    outer_param_2: float = None  # either dtheta (°) or height (m)
    inner_param_1: float = None  # either radius (m) or width (m)
    inner_param_2: float = None  # either dtheta (°) or height (m)

    def __init__(self, name: str, _type: str, position: tuple = (0, 0, 0), orientation: tuple = (0, 0, 0),
                 radius: float = None, dtheta: float = 180, dx: float = None, dy: float = None,
                 save_avg_data: bool = False, save_ind_data: bool = False, avg_grid: tuple[int, ...] = None):

        """
        :param name: name of the planepiece
        :param position: position (x, y, z) in m
        :param orientation: orientation (phi, theta, psi) in °
        :param _type: type of the plane, either "circle" or "c" for a circle or "rectangle" or "r" for a rectangle
        :param radius: radius of the circle in m
        :param dtheta: opening angle of the circle in °, defaults to a full circle
        :param dx: half width of the rectangle in m
        :param dy: half height of the rectangle in m
        :param save_avg_data: whether the average data should be saved, defaults to False
        :param save_ind_data: whether the individual data should be saved, defaults to False
        :param avg_grid: averaging grid size, tuple with number of segments in x and y direction. Ignored if
            save_avg_data is False
        """

        # Initialize the superclass
        super().__init__(name, position, orientation, save_avg_data, save_ind_data, avg_grid)
        # Check if the types and input parameters are correct
        self._check(_type, radius, dtheta, dx, dy, reason='creating')
        # Store the type of the plane, replace the short versions with the long ones
        self.plane_type = 'rectangle' if _type == 'r' else 'circle' if _type == 'c' else _type
        # Store the specific parameters inside the class
        self.outer_param_1 = radius if _type in ['circle', 'c'] else dx
        self.outer_param_2 = dtheta if _type in ['circle', 'c'] else dy

    @staticmethod
    def _check(_type: str, radius: float, dtheta: float, dx: float, dy: float, reason: str):

        """
        Performs a type check for defining the plane or the perforating plane and checks if the right combination of
        parameters was set. Throws a ValueError if check not successful.

        :param _type: type of the plane, either "circle" or "c" for a circle or "rectangle" or "r" for a rectangle
        :param radius: radius of the circle in m
        :param dtheta: opening angle of the circle in °
        :param dx: half width of the rectangle in m
        :param dy: half height of the rectangle in m
        :param reason: reason for the type check
        """

        # Check if the type is correct
        if _type not in ['circle', 'c', 'rectangle', 'r']:
            raise ValueError('The type either needs to be "circle"/"c" or "rectangle"/"r", not %s.' % type)
            # Check if the correct parameters were set for the perforation type
        if _type in ['circle', 'c'] and (radius is None or dtheta is None):
            raise ValueError('For %s a circle, both the radius and the opening angle need to be set.' % reason)
        if _type in ['rectangle', 'r'] and (dx is None or dy is None):
            raise ValueError('For %s a rectangle, both the dx and dy need to be set.' % reason)

    def perforate(self, by: str, radius: float = None, dtheta: float = 180, dx: float = None, dy: float = None):

        """
        Perforates the plane either by a circle or a rectangle.

        :param by: either "circle" or "c" for perforating with a circle or "rectangle" or "r" for perforating with a
        rectangle
        :param radius: radius of the circle in m, required when perforating with a circle
        :param dtheta: opening angle of the circle in °, defaults to 180° being a full circle, required when
        perforating with a circle. This needs to be identical to the outer opening angle of the circle
        :param dx: half width of the rectangle in m, required when perforating with a rectangle
        :param dy: half height of the rectangle in m, required when perforating with a rectangle
        """

        # Check if the types and input parameters are correct
        self._check(by, radius, dtheta, dx, dy, reason='perforating with')
        # Store the perforation type
        self.perforation_type = 'rectangle' if by == 'r' else 'circle' if by == 'c' else by
        # Set the inner parameters of the class
        self.inner_param_1 = radius if by in ['circle', 'c'] else dx
        self.inner_param_2 = dtheta if by in ['circle', 'c'] else dy
