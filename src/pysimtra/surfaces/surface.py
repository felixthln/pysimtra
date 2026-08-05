

class Surface:

    """
    Base class for all SIMTRA surfaces.
    """

    def __init__(self, name: str, position: tuple = (0, 0, 0), orientation: tuple = (0, 0, 0),
                 save_avg_data: bool = False, save_ind_data: bool = False, avg_grid: tuple[int, ...] = None):

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
        self.avg_grid: tuple[int, ...] = avg_grid
