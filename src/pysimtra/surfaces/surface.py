

class Surface:

    """
    Base class for all SIMTRA surfaces.
    """

    # Internal SIMTRA representation
    simtra_type: str = None
    # Name of the surface
    name: str = None
    # Position and orientation of the surface
    position: tuple = None  # (x, y, z) in m
    orientation: tuple = None  # (phi, theta, psi) in °
    # Particle saving preferences
    save_avg_data: bool = None
    save_ind_data: bool = None
    avg_grid: tuple[int, ...] = None

    def __init__(self, name: str, position: tuple = (0, 0, 0), orientation: tuple = (0, 0, 0),
                 save_avg_data: bool = False, save_ind_data: bool = False, avg_grid: tuple[int, ...] = None):
        # Store the properties inside the class
        self.name = name
        self.position = position
        self.orientation = orientation
        self.save_avg_data = save_avg_data
        self.save_ind_data = save_ind_data
        self.avg_grid = avg_grid
