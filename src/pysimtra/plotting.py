import warnings
import numpy as np

from .surfaces import Surface, Plane, Cylinder, Cone, Sphere
from .components import Chamber, Magnetron, DummyObject
from .transforms import local_basis


# Default colors of the different parts of a sputter system
DEFAULT_COLORS: dict[str, str] = {
    'chamber': '0.75',  # walls of the sputter chamber
    'magnetron': 'tab:blue',  # surfaces making up a magnetron
    'sputter_surface': 'tab:red',  # surface of a magnetron the particles are launched from
    'object': 'tab:green',  # surfaces of a dummy object
    'detector': 'tab:orange'  # surfaces of a dummy object that store the averaged data
}

# Labels used in the legend
LEGEND_LABELS: dict[str, str] = {
    'chamber': 'chamber',
    'magnetron': 'magnetron',
    'sputter_surface': 'sputter surface',
    'object': 'dummy object',
    'detector': 'dummy object (saving data)'
}

# Order in which the categories are drawn. Neighbouring surfaces frequently share an edge exactly, e.g. the shield of a
# magnetron starts at the rim of its target, so the highlighted surfaces have to be drawn last to stay visible
DRAW_ORDER: dict[str, int] = {'chamber': 0, 'magnetron': 1, 'object': 1, 'sputter_surface': 2, 'detector': 2}


# :- Private supporting functions


# Function to import pyplot only when it is actually needed, matplotlib is an optional dependency
def import_pyplot():
    try:
        import matplotlib.pyplot as plt
    except ImportError as e:
        raise ImportError('Plotting requires matplotlib, which is not installed. Install it via "pip install '
                          'matplotlib".') from e
    return plt


# Function to calculate the angles of an arc from a SIMTRA opening angle
def arc_angles(dtheta: float, n_points: int) -> np.ndarray:
    # In SIMTRA the opening angle is measured in both directions, so a value of 180° describes a full circle
    if abs(dtheta) >= 180 - 1e-9:
        return np.linspace(-np.pi, np.pi, n_points)
    # For a partial shape, only sweep between the two opening angles
    return np.linspace(-np.radians(dtheta), np.radians(dtheta), n_points)


# Function to calculate the angles at which a cylinder or a cone is connected by a line
def connector_angles(dtheta: float, n_connectors: int) -> np.ndarray:
    # For a full shape, distribute the connectors evenly without repeating the first one
    if abs(dtheta) >= 180 - 1e-9:
        return np.linspace(-np.pi, np.pi, n_connectors, endpoint=False)
    # For a partial shape, include both ends so the opening becomes visible
    return np.linspace(-np.radians(dtheta), np.radians(dtheta), n_connectors)


# Function to create a ring or an arc in the local xy plane at a given height
def arc(radius: float, dtheta: float, n_points: int, z: float = 0.0) -> np.ndarray:
    # Calculate the angles and convert them into points
    angles = arc_angles(dtheta, n_points)
    return np.column_stack((radius * np.cos(angles), radius * np.sin(angles), np.full(angles.shape, float(z))))


# Function to create a closed rectangle in the local xy plane from a half width and a half height
def rectangle_outline(dx: float, dy: float) -> np.ndarray:
    return np.array([[-dx, -dy, 0], [dx, -dy, 0], [dx, dy, 0], [-dx, dy, 0], [-dx, -dy, 0]], dtype=float)


# Function to create the outlines of a plane, which is either a circle or a rectangle and might be perforated
def plane_outlines(sur: Plane, n_points: int) -> list[np.ndarray]:
    outlines: list[np.ndarray] = []
    # For a rectangle the two outer parameters are the half width and the half height, for a circle the radius and
    # the opening angle
    if sur.plane_type == 'rectangle':
        outlines.append(rectangle_outline(sur.outer_param_1, sur.outer_param_2))
    else:
        outlines.append(arc(sur.outer_param_1, sur.outer_param_2, n_points))
    # Add the perforation, which is described by the two inner parameters in the same way
    if sur.perforation_type == 'rectangle':
        outlines.append(rectangle_outline(sur.inner_param_1, sur.inner_param_2))
    elif sur.perforation_type == 'circle':
        outlines.append(arc(sur.inner_param_1, sur.inner_param_2, n_points))
    # A partial circle is closed by connecting both ends of the arc, either with the perforation or with the center
    if sur.plane_type == 'circle' and abs(sur.outer_param_2) < 180 - 1e-9:
        inner_radius = sur.inner_param_1 if sur.perforation_type == 'circle' else 0.0
        angles = arc_angles(sur.outer_param_2, n_points)
        for angle in [angles[0], angles[-1]]:
            direction = np.array([np.cos(angle), np.sin(angle), 0.0])
            outlines.append(np.vstack((inner_radius * direction, sur.outer_param_1 * direction)))
    return outlines


# Function to create the outlines of a cylinder, drawn as two rings connected by a few lines
def cylinder_outlines(sur: Cylinder, n_points: int, n_connectors: int) -> list[np.ndarray]:
    # A cylinder starts at its position and grows along the local z axis
    outlines = [arc(sur.radius, sur.dtheta, n_points, z=0.0), arc(sur.radius, sur.dtheta, n_points, z=sur.height)]
    # Connect both rings with vertical lines to make the shape readable
    for angle in connector_angles(sur.dtheta, n_connectors):
        point = np.array([sur.radius * np.cos(angle), sur.radius * np.sin(angle), 0.0])
        outlines.append(np.vstack((point, point + np.array([0.0, 0.0, sur.height]))))
    return outlines


# Function to create the outlines of a cone, drawn as two rings of different radius connected by a few lines
def cone_outlines(sur: Cone, n_points: int, n_connectors: int) -> list[np.ndarray]:
    # The small radius sits at the position of the cone, the big one at the far end along the local z axis
    outlines = [arc(sur.small_rho, sur.dtheta, n_points, z=0.0), arc(sur.big_rho, sur.dtheta, n_points, z=sur.height)]
    # Connect both rings along the lateral surface
    for angle in connector_angles(sur.dtheta, n_connectors):
        direction = np.array([np.cos(angle), np.sin(angle), 0.0])
        outlines.append(np.vstack((sur.small_rho * direction,
                                   sur.big_rho * direction + np.array([0.0, 0.0, sur.height]))))
    return outlines


# Function to scale all three axes of a 3D plot identically, so the system does not appear distorted
def set_equal_aspect(ax, points: np.ndarray):
    # Get the extent of the drawn geometry
    lower, upper = points.min(axis=0), points.max(axis=0)
    ranges = upper - lower
    # A single flat surface has no extent along one axis, which matplotlib cannot handle. Pad those axes with a
    # fraction of the overall size of the geometry, or with a fixed value if the geometry is a single point
    padding = np.max(ranges) * 0.05 if np.max(ranges) > 0 else 1.0
    flat = ranges <= 0
    lower = np.where(flat, lower - padding, lower)
    upper = np.where(flat, upper + padding, upper)
    # Set the limits and shape the box like the data, which scales all three axes identically
    ax.set_xlim(lower[0], upper[0])
    ax.set_ylim(lower[1], upper[1])
    ax.set_zlim(lower[2], upper[2])
    ax.set_box_aspect(tuple(upper - lower))


# Function to label the three axes of a 3D plot
def set_axis_labels(ax):
    ax.set_xlabel('x [m]')
    ax.set_ylabel('y [m]')
    ax.set_zlabel('z [m]')


# Function to flip the view of a 3D plot upside down
def set_sputter_direction(ax, sputter_up: bool):
    # SIMTRA always launches the particles along the positive z axis, but a real chamber might be built the other way
    # around. Reversing the z axis turns the system upside down without touching the geometry itself. Mirroring the
    # elevation of the view does not achieve this, it only moves the camera below the chamber while matplotlib keeps
    # projecting the z axis upwards
    if not sputter_up:
        lower, upper = ax.get_zlim()
        ax.set_zlim(upper, lower)


# Function to add a legend below the plot, so it does not cover the system
def add_legend(ax, n_columns: int = 2):
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=n_columns, fontsize='small')


# :- Public functions used in the other classes


def surface_outlines(sur: Surface, n_points: int = 64, n_connectors: int = 4) -> list[np.ndarray]:

    """
    Creates the wireframe outlines of a surface in its own coordinate system.

    :param sur: Surface object
    :param n_points: number of points used to draw a full circle
    :param n_connectors: number of lines connecting the two rings of a cylinder or a cone
    :return: list of polylines, each being an array of shape (N, 3)
    """

    # The order of the checks matters, Circle and Rectangle are subclasses of Plane
    if isinstance(sur, Plane):
        return plane_outlines(sur, n_points)
    elif isinstance(sur, Cylinder):
        return cylinder_outlines(sur, n_points, n_connectors)
    elif isinstance(sur, Cone):
        return cone_outlines(sur, n_points, n_connectors)
    # Spheres are not drawn yet. Since they may well appear in a ".sin" file written by the SIMTRA GUI, only warn about
    # them instead of raising an error, so the rest of the system can still be displayed
    elif isinstance(sur, Sphere):
        warnings.warn('The sphere "%s" is not displayed, plotting of spheres is not implemented yet.' % sur.name)
        return []
    raise ValueError('The type of the surface "%s" could not be identified.' % sur.name)


def transform(points: np.ndarray, position: tuple, orientation: tuple) -> np.ndarray:

    """
    Transforms points from a local coordinate system into the surrounding one.

    :param points: array of shape (N, 3) holding the points to transform
    :param position: position (x, y, z) of the local coordinate system in m
    :param orientation: orientation (phi, theta, psi) of the local coordinate system in °
    :return: array of shape (N, 3) holding the transformed points
    """

    # "local_basis" returns the basis vectors a, b and c as its rows, so multiplying from the right rotates every point
    return np.asarray(position, dtype=float) + points @ local_basis(orientation)


def surface_polylines(sur: Surface, obj_position: tuple = (0, 0, 0), obj_orientation: tuple = (0, 0, 0),
                      n_points: int = 64, n_connectors: int = 4) -> list[np.ndarray]:

    """
    Creates the wireframe outlines of a surface in the coordinate system of the chamber. Since a surface is positioned
    relative to the dummy object it belongs to, both transformations are applied one after another.

    :param sur: Surface object
    :param obj_position: position (x, y, z) of the dummy object the surface belongs to, in m
    :param obj_orientation: orientation (phi, theta, psi) of the dummy object the surface belongs to, in °
    :param n_points: number of points used to draw a full circle
    :param n_connectors: number of lines connecting the two rings of a cylinder or a cone
    :return: list of polylines, each being an array of shape (N, 3)
    """

    # First transform from the surface into the object coordinate system, then into the one of the chamber
    return [transform(transform(outline, sur.position, sur.orientation), obj_position, obj_orientation)
            for outline in surface_outlines(sur, n_points, n_connectors)]


def object_polylines(obj: DummyObject, n_points: int = 64,
                     n_connectors: int = 4) -> list[tuple[Surface, list[np.ndarray]]]:

    """
    Creates the wireframe outlines of all surfaces of a dummy object in the coordinate system of the chamber.

    :param obj: DummyObject object
    :param n_points: number of points used to draw a full circle
    :param n_connectors: number of lines connecting the two rings of a cylinder or a cone
    :return: list of tuples, each holding a surface and the list of its polylines
    """

    return [(sur, surface_polylines(sur, obj.position, obj.orientation, n_points, n_connectors))
            for sur in obj.surfaces]


def chamber_polylines(ch: Chamber, n_points: int = 64, n_connectors: int = 4) -> list[np.ndarray]:

    """
    Creates the wireframe outlines of a sputter chamber. The chamber defines the coordinate system of the simulation,
    it is centered around the z axis and spans from z = 0 to z = length.

    :param ch: Chamber object
    :param n_points: number of points used to draw a full circle
    :param n_connectors: number of lines connecting the bottom and the top of a cylindrical chamber
    :return: list of polylines, each being an array of shape (N, 3)
    """

    # A cylindrical chamber is drawn as two rings connected by a few vertical lines
    if ch.shape == 'cylinder':
        outlines = [arc(ch.radius, 180, n_points, z=0.0), arc(ch.radius, 180, n_points, z=ch.length)]
        for angle in connector_angles(180, n_connectors):
            point = np.array([ch.radius * np.cos(angle), ch.radius * np.sin(angle), 0.0])
            outlines.append(np.vstack((point, point + np.array([0.0, 0.0, ch.length]))))
        return outlines
    # A cuboid chamber is drawn by its twelve edges, the height points in x and the width in y direction
    elif ch.shape == 'cuboid':
        dx, dy = ch.height / 2, ch.width / 2
        corners = [(-dx, -dy), (dx, -dy), (dx, dy), (-dx, dy), (-dx, -dy)]
        # Add the bottom and the top face
        outlines = [np.array([[x, y, z] for x, y in corners], dtype=float) for z in [0.0, ch.length]]
        # Add the four vertical edges
        for x, y in corners[:4]:
            outlines.append(np.array([[x, y, 0.0], [x, y, ch.length]], dtype=float))
        return outlines
    raise ValueError('The chamber shape "%s" could not be identified.' % ch.shape)


def plot_system(chamber: Chamber = None, magnetrons: Magnetron | list[Magnetron] = None,
                dummy_objects: DummyObject | list[DummyObject] = None, ax=None, n_points: int = 64,
                n_connectors: int = 4, colors: dict[str, str] = None, show_legend: bool = True,
                equal_aspect: bool = True, sputter_up: bool = True, **kwargs):

    """
    Draws a sputter system as a 3D wireframe model, mimicking the display of the SIMTRA graphical user interface. In
    contrast to the GUI, all magnetrons of a multi-cathode system are displayed at once.

    :param chamber: Chamber object, may be omitted to only display the components
    :param magnetrons: either a single magnetron object or a list of magnetrons
    :param dummy_objects: either a single dummy object or a list of dummy objects
    :param ax: matplotlib 3D axes to draw on. If not given, a new figure and axes are created
    :param n_points: number of points used to draw a full circle
    :param n_connectors: number of lines connecting the two rings of a cylinder or a cone
    :param colors: mapping overriding single entries of DEFAULT_COLORS
    :param show_legend: whether a legend should be added below the plot
    :param equal_aspect: whether all three axes should be scaled identically, which is needed for the system to not
        appear distorted
    :param sputter_up: whether the particles travel upwards in the figure. SIMTRA always launches them along the
        positive z axis and does not care how the chamber is built, so set this to False to display a chamber whose
        magnetrons sputter downwards
    :param kwargs: further keyword arguments passed on to the matplotlib "plot" function, e.g. "linewidth"
    :return: the matplotlib axes the system was drawn on
    """

    plt = import_pyplot()
    # Create a new figure with 3D axes if none was passed
    if ax is None:
        fig = plt.figure(figsize=(5, 6.1))
        ax = fig.add_subplot(projection='3d')
        fig.subplots_adjust(bottom=0.2, top=0.95)
    # Merge the given colors with the default ones
    style = dict(DEFAULT_COLORS, **(colors if colors else {}))
    # Wrap single components in a list and treat None as an empty list
    magnetrons = [magnetrons] if isinstance(magnetrons, Magnetron) else list(magnetrons) if magnetrons else []
    dummy_objects = [dummy_objects] if isinstance(dummy_objects, DummyObject) else \
        list(dummy_objects) if dummy_objects else []
    # Collect all polylines together with the category they belong to
    lines: list[tuple[str, np.ndarray]] = []
    # Add the chamber
    if chamber is not None:
        lines += [('chamber', line) for line in chamber_polylines(chamber, n_points, n_connectors)]
    # Add the magnetrons, highlighting the surface the particles are launched from
    for mag in magnetrons:
        for i, (sur, polylines) in enumerate(object_polylines(mag.m_object, n_points, n_connectors), 1):
            # The sputter surface index begins at 1
            category = 'sputter_surface' if i == mag.sputter_surface_index else 'magnetron'
            lines += [(category, line) for line in polylines]
    # Add the dummy objects, highlighting the surfaces which store the averaged particle data
    for obj in dummy_objects:
        for sur, polylines in object_polylines(obj, n_points, n_connectors):
            category = 'detector' if sur.save_avg_data else 'object'
            lines += [(category, line) for line in polylines]
    # Draw the highlighted surfaces last so they are not overdrawn by a neighbouring surface sharing their edge
    lines.sort(key=lambda item: DRAW_ORDER.get(item[0], 1))
    # Draw everything, labelling only the first line of every category so the legend stays free of duplicates
    labelled: set[str] = set()
    for category, line in lines:
        label = None
        if category not in labelled:
            label = LEGEND_LABELS.get(category, category)
            labelled.add(category)
        ax.plot(line[:, 0], line[:, 1], line[:, 2], color=style.get(category), label=label, **kwargs)
    # Label the axes
    set_axis_labels(ax)
    # Scale all axes identically
    if equal_aspect and lines:
        set_equal_aspect(ax, np.vstack([line for _, line in lines]))
    # Turn the system upside down if the magnetrons sputter downwards
    set_sputter_direction(ax, sputter_up)
    # Add the legend below the plot
    if show_legend and labelled:
        add_legend(ax)
    return ax


def plot_object(obj: DummyObject, ax=None, color: str = None, highlight_index: int = None,
                highlight_color: str = None, label: str = None, n_points: int = 64, n_connectors: int = 4,
                equal_aspect: bool = True, sputter_up: bool = True, **kwargs):

    """
    Draws a single dummy object as a 3D wireframe model. This is mostly useful while building a component, in order to
    check it on its own before adding it to a sputter system.

    :param obj: DummyObject object
    :param ax: matplotlib 3D axes to draw on. If not given, a new figure and axes are created
    :param color: color of the surfaces, defaults to the color used for dummy objects
    :param highlight_index: index of a surface to draw in the highlight color, beginning at 1 as in SIMTRA
    :param highlight_color: color of the highlighted surface
    :param label: label of the object used in the legend
    :param n_points: number of points used to draw a full circle
    :param n_connectors: number of lines connecting the two rings of a cylinder or a cone
    :param equal_aspect: whether all three axes should be scaled identically
    :param sputter_up: whether the particles travel upwards in the figure. SIMTRA always launches them along the
        positive z axis and does not care how the chamber is built, so set this to False to display a component of a
        chamber whose magnetrons sputter downwards
    :param kwargs: further keyword arguments passed on to the matplotlib "plot" function
    :return: the matplotlib axes the object was drawn on
    """

    plt = import_pyplot()
    # Create a new figure with 3D axes if none was passed
    if ax is None:
        fig = plt.figure(figsize=(5, 6.1))
        ax = fig.add_subplot(projection='3d')
        fig.subplots_adjust(bottom=0.2, top=0.95)
    # Fall back to the default colors
    color = DEFAULT_COLORS['object'] if color is None else color
    highlight_color = DEFAULT_COLORS['sputter_surface'] if highlight_color is None else highlight_color
    # Collect the surfaces and draw the highlighted one last, so it is not overdrawn by a neighbouring surface sharing
    # its edge, e.g. the shield of a magnetron which starts at the rim of its target
    surfaces = list(enumerate(object_polylines(obj, n_points, n_connectors), 1))
    surfaces.sort(key=lambda item: 1 if item[0] == highlight_index else 0)
    # Draw every surface, labelling only the very first line
    all_lines: list[np.ndarray] = []
    labelled = False
    for i, (sur, polylines) in surfaces:
        is_highlighted = highlight_index is not None and i == highlight_index
        for line in polylines:
            ax.plot(line[:, 0], line[:, 1], line[:, 2], color=highlight_color if is_highlighted else color,
                    label=None if labelled else label, **kwargs)
            labelled = True
            all_lines.append(line)
    # Label the axes
    set_axis_labels(ax)
    # Scale all axes identically
    if equal_aspect and all_lines:
        set_equal_aspect(ax, np.vstack(all_lines))
    # Turn the object upside down if the magnetrons sputter downwards
    set_sputter_direction(ax, sputter_up)
    # Add a legend below the plot if the object was labelled
    if label:
        add_legend(ax)
    return ax