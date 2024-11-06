import numpy as np
from pathlib import Path

from .surfaces import Surface, Circle, Rectangle, Cylinder, Cone, Sphere
from .components import Chamber, Magnetron, DummyObject


# :- Private supporting functions


# Function which normalizes a given vector x
def normalize(x: np.array) -> np.array:
    return x / np.linalg.norm(x)


# Function to calculate the length of a vector
def length(x: np.array) -> np.array:
    return np.sqrt(np.sum(x ** 2))


# Calculate the 4d rotation matrix of a shape based on the saved 3d matrix of a SIMTRA file
def calc_rot_mat(shape_type: str, mat: np.array) -> np.array:
    # Calculate the a, b and c depending on the respective SIMTRA shape type
    if shape_type == 'cylinderpiece':
        a = normalize(mat[2] - mat[0])
        c = normalize(mat[1] - mat[0])
        b = np.cross(c, a)
    elif shape_type == 'planepiece':
        a = normalize(mat[1] - mat[0])
        b = normalize(mat[2] - mat[0])
        c = np.cross(a, b)
    elif shape_type == 'conepiece':
        a = normalize(mat[2] - mat[1])
        c = normalize(mat[1] - mat[0])
        b = np.cross(c, a)
    elif shape_type == 'spherepiece':
        a = normalize(mat[2] - mat[0])
        c = normalize(mat[1] - mat[0])
        b = np.cross(c, a)
    else:
        raise ValueError('The shape type could not be identified.')
    # Stack the results together as rows
    return np.vstack((np.append(a, 0.0), np.append(b, 0.0), np.append(c, 0.0), np.append(mat[0], 1.0)))


# Calculate the used euler angles from a 4d rotation matrix
def calc_angles(rot_mat: np.array) -> np.array:
    # First handle the normal case
    if np.abs(rot_mat[2, 2]) < 0.9999999:
        # Calculate the angles
        theta = np.arccos(rot_mat[2, 2])
        psi = np.arctan2(rot_mat[1, 2] / np.sin(theta), - rot_mat[0, 2] / np.sin(theta))
        phi = np.arctan2(rot_mat[2, 1] / np.sin(theta), rot_mat[2, 0] / np.sin(theta))
        # Convert the angles and return them
        return np.around(np.array([phi, theta, psi]) / np.pi * 180, 3)
    else:
        # Set the psi angle to zero
        phi = 0
        if rot_mat[2, 2] >= 0.9999999:
            # Also set theta to zero
            theta = 0
            psi = np.arctan2(rot_mat[1, 0], rot_mat[0, 0])
        else:
            theta = np.pi
            psi = np.arctan2(rot_mat[1, 0], rot_mat[1, 1])
        # Convert the angles and return them
        return np.around(np.array([phi, theta, psi]) / np.pi * 180, 3)


def parse_chamber(lines: list[str]) -> Chamber:

    """
    Parses a list of lines from a SIMTRA input file to extract a chamber object.

    :param lines: list of lines from the SIMTRA input file
    :return: Chamber object
    """

    # Find the index of the first parameter, and the one of the last in this section
    start_index = lines.index('\'chamber   ---------------------------------------\n') + 2
    end_index = lines.index('\'Source   ----------------------------------------\n') - 3
    # Get the shape of the chamber
    shape = lines[start_index][30:].rstrip()
    # Get the geometrical chamber parameters
    chamber_params = lines[start_index + 1][30:].rstrip().split(' ')[:-1]
    # Split them based on the chamber shape
    _length, radius, width, height = [None] * 4
    if shape == 'cuboid':
        height, width, _length = [float(i) for i in chamber_params]  # m
    elif shape == 'cylinder':
        radius, _length = [float(i) for i in chamber_params]  # m
    # Get the rest of the parameters
    temperature = float(lines[start_index + 2][30:].rstrip().split(' ')[0])  # K
    pressure = float(lines[start_index + 3][30:].rstrip().split(' ')[0])  # Pa
    gas_element = lines[start_index + 4][30:].rstrip()
    seed_number = int(lines[start_index + 5][30:].rstrip())
    chamber_walls_grid = tuple(int(i) for i in lines[start_index + 6][30:].rstrip().split(' '))
    # The 'saveDepositionWall' parameter is optional and might not have a value
    save_deposition_walls = []
    if lines[start_index + 7][30:] != '\n':
        save_deposition_walls = [int(i) for i in lines[start_index + 7][30:].rstrip().split(' ')]
    # The 'saveIndividualData' parameter is optional and is only there if the feature is turned on
    # Check if the section is long enough to have this parameter
    save_individual_data = end_index - start_index + 1 == 9
    # Construct the chamber object and return it
    return Chamber(shape, _length, temperature, pressure, gas_element, radius, height, width, seed_number,
                   chamber_walls_grid, save_deposition_walls, save_individual_data)


# Parse a single surface and its parameters
def parse_surface(lines: list[str]) -> Surface:

    """
    Parses a list of lines from a SIMTRA input file to extract a surface object.

    :param lines: list of lines from the SIMTRA input file
    :return: Surface object
    """

    # Get the surface type and name
    surf_type = lines[0][:30].rstrip()
    name = lines[0][30:].rstrip()
    # Get the position and rotation information of the surface
    r1 = np.array([float(i) for i in lines[1].split(' ')])
    r2 = np.array([float(i) for i in lines[2].split(' ')])
    r3 = np.array([float(i) for i in lines[3].split(' ')])
    mat = np.array([r1, r2, r3])
    # Get the surface parameters
    surf_params = [float(i) for i in lines[4].rstrip().split(' ')]
    # Store the position of the surface, given by the first row (r1)
    pos = r1.tolist()
    # Calculate the rotation matrix and extract the Euler angles (phi, theta, psi)
    rot_mat = calc_rot_mat(surf_type, mat)
    orient = calc_angles(rot_mat).tolist()
    # Check whether deposition information on the surface should be stored or not
    dep_params = lines[5].rstrip().split(' ')
    # Save whether the deposition information should be saved (by default, deactivate all)
    save_avg_data = dep_params[0] == '1' or dep_params[0] == '3'
    save_ind_data = dep_params[0] == '2' or dep_params[0] == '3'
    # Save the grid parameters if the averaged data should be saved
    avg_grid = (int(dep_params[1]), int(dep_params[2])) if save_avg_data else None
    # Define the surface variable, which will be a subclass of the Surface class
    surf: Circle | Rectangle | Cylinder | Cone | Sphere | None = None
    # Get the rest of the parameters based on the surface type
    if surf_type == 'planepiece':
        # Define whether the planepiece is a circle or rectangle
        _type = 'circle' if surf_params[0] == 2 else 'rectangle'
        # Create a circle or rectangle object
        if _type == 'circle':
            # Get the radius and opening angle
            radius, dtheta = surf_params[2:4]  # m, °
            # Create the object
            surf = Circle(name, radius, pos, orient, dtheta, save_avg_data, save_ind_data, avg_grid)
        elif _type == 'rectangle':
            # Get the width and height
            dx, dy = surf_params[2:4]  # m
            # Create the object
            surf = Rectangle(name, dx, dy, pos, orient, save_avg_data, save_ind_data, avg_grid)
        # Perforate if defined
        if surf_params[1] != 0:
            # Get the perforation type
            by = 'circle' if surf_params[1] == 2 else 'rectangle' if surf_params[1] == 1 else None
            # Define either the radius and opening angle for a circle, or the width and height for the rectangle
            radius, dtheta, dx, dy = [None] * 4
            if by == 'circle':
                radius, dtheta = surf_params[4:6]  # m, °
            elif by == 'rectangle':
                dx, dy = surf_params[4:6]  # m
            # Perform the perforation
            surf.perforate(by, radius, dtheta, dx, dy)
    # If the surface type is a cylinder
    elif surf_type == 'cylinderpiece':
        # Store the height and the radius by extracting them from the given matrix
        radius = np.around(length(r3 - r1), 6)
        height = np.around(length(r2 - r1), 6)
        # Store the opening angle
        dtheta = float(lines[4])
        # Create the Cylinder
        surf = Cylinder(name, radius, height, pos, orient, dtheta, save_avg_data, save_ind_data, avg_grid)
    # If the surface type is a cone
    elif surf_type == 'conepiece':
        # Get the inner radius from the surface parameters
        small_rho = surf_params[0]
        # Store the large radius and the height by extracting them from the given matrix
        big_rho = np.around(length(r3 - r2), 6)
        height = np.around(length(r2 - r1), 6)
        # Store the opening angle
        dtheta = float(surf_params[1])
        # Create the Cone
        surf = Cone(name, small_rho, big_rho, height, pos, orient, dtheta, save_avg_data, save_ind_data, avg_grid)
    # If the surface type is a sphere
    elif surf_type == 'spherepiece':
        # Extract the radius from the given matrix
        radius = np.around(length(r2 - r1), 6)
        # Store the two opening angles
        dphi, dtheta = float(surf_params[0]), float(surf_params[1])
        # Create the Sphere
        surf = Sphere(name, radius, dphi, pos, orient, dtheta, save_avg_data, save_ind_data, avg_grid)
    # Return the surface
    return surf


# Parse all parameters of an object
def parse_object(lines: list[str]) -> DummyObject:
    # Parse the name of the object
    name = lines[0][30:].rstrip().split(' ')[0]
    # Retrieve the general parameters
    pos = tuple(float(i) for i in lines[1][30:].rstrip().split(' '))  # m
    orient = tuple(float(i) for i in lines[2][30:].rstrip().split(' '))  # °
    # Get the number of sub objects
    n_objects = int(len(lines[5:]) / 7)
    # Parse all sub objects which can be either: "cylinderpiece", "planepiece" or "conepiece"
    surfaces = []
    for i in range(n_objects):
        # Parse the current sub object and add it to the list
        surfaces.append(parse_surface(lines[i * 7 + 5:(i + 1) * 7 + 5]))
    # Create the object
    return DummyObject(name, surfaces, pos, orient)


# Parse all magnetron parameters
def parse_magnetron(lines: list[str]) -> Magnetron:
    # Get all general parameters in this section
    transported_element = lines[0][30:].rstrip()
    inter_potential = lines[1][30:].rstrip()
    # Get the scattering table location when the SRIM is used for the angular distribution
    scat_table_path = lines[2][30:].rstrip() if inter_potential == 'specified' else None
    # If screened coulomb is selected, store the screening function
    screening_function = lines[2][30:].rstrip() if inter_potential == 'screenedCoulomb' else None
    # Get the other parameters
    with_gas_motion = lines[3][30:].rstrip() == 'yes'
    go_to_diffusion = lines[4][30:].rstrip() == 'yes'
    source_type = lines[5][30:].rstrip()
    # Store the number of particles and after how many particles the values should be saved
    particles = lines[6][30:].rstrip().split(' ')
    n_particles, save_every = int(particles[0]), int(particles[1])
    # Get the energy distribution
    energy_distribution = lines[7][30:].rstrip()
    # Store the surface binding energy and the maximum ion energy
    surface_binding_energy = float(lines[8][30:].rstrip().split(' ')[0])  # eV
    # Introduce a shift index which is important when the energy distribution is defined by SRIM
    shift_index = 0
    # Check if the energy distribution is a modelled by a Thompson distribution or defined by SRIM
    max_ion_energy = float(lines[9][30:].rstrip().split(' ')[0]) if energy_distribution == 'Thompson' else None  # [eV]
    # If the energy distribution is defined by SRIM, store the type and the file
    srim_type, srim_file_path = None, None
    if energy_distribution == 'SRIM':
        srim_type, srim_file_path = lines[9][30:].rstrip(), lines[10][30:].rstrip()
        # The text file is one line larger when SRIM was selected, therefore increase the start index
        shift_index += 1
    # Get the angular distribution
    angular_distribution = lines[shift_index + 10][30:].rstrip()
    # When the angular distribution was defined by a user defined cosine distribution, store the coefficients
    cosine_coefficients = None
    if angular_distribution == 'User':
        cosine_coefficients = tuple(float(i) for i in lines[shift_index + 11][30:].rstrip().split(' '))
        # The text file is one line larger when the user defined angular distribution was selected
        shift_index += 1
    # Find the end index of the object definition by searching for the closing bracket
    mag_end_index = lines.index('}\n')
    # Parse the magnetron object and get the name of the object
    mag_object = parse_object(lines[shift_index + 11:mag_end_index])
    # Store from which surface the particles should be sputtered
    sputter_surface_index = int(lines[mag_end_index + 2][30:].rstrip())
    # Store racetrack t0 (whatever this means)
    r_t0 = int(lines[mag_end_index + 3][30:].rstrip())
    # Store the path to the racetrack file
    r_file_path = lines[mag_end_index + 4][30:].rstrip()
    # Get the racetrack type
    r_type = lines[mag_end_index + 5][30:].rstrip()
    # If the racetrack type is "profilometry", store the row and column resolution
    r_row_res, r_col_res = None, None
    if r_type == 'profilometry':
        r_row_res = int(lines[mag_end_index + 6][30:].rstrip())
        r_col_res = int(lines[mag_end_index + 7][30:].rstrip())
    # Finally, create the Magnetron object
    return Magnetron(source_type=source_type, transported_element=transported_element, n_particles=n_particles,
                     sputter_surface_index=sputter_surface_index, racetrack_file_path=r_file_path,
                     racetrack_type=r_type, angular_distribution=angular_distribution,
                     interaction_potential=inter_potential, energy_distribution=energy_distribution,
                     m_object=mag_object, save_every_n_particles=save_every, racetrack_t0=r_t0,
                     racetrack_row_res=r_row_res, racetrack_col_res=r_col_res, cosine_coefficients=cosine_coefficients,
                     srim_type=srim_type, srim_file_path=srim_file_path, with_gas_motion=with_gas_motion,
                     go_to_diffusion=go_to_diffusion, screening_function=screening_function,
                     scattering_table_path=scat_table_path, surface_binding_energy=surface_binding_energy,
                     max_ion_energy=max_ion_energy)


# Parse all dummy objects and retrieve their parameters
def parse_dummy_objects(lines: list[str]) -> list[DummyObject]:
    # Store the objects in a list of dictionaries
    objects = []
    # Find the index of the first object, and the one of the last in this section
    start_index = lines.index('\'objects   ---------------------------------------\n') + 2
    final_index = lines.index('\'movement   --------------------------------------\n') - 2
    # Only keep the relevant lines
    lines_obj = lines[start_index:final_index]
    # Get the number of dummy objects by counting getting the indices of all closing brackets
    end_indices = [i for i, x in enumerate(lines_obj) if x == '}\n']
    # Iterate over all dummy objects
    for i, index in enumerate(end_indices):
        # If it is the first object, start from the start index, otherwise from the previous end index
        start_ind = 0 if i == 0 else end_indices[i - 1] + 2
        # Parse the rest of the object and add it to the list
        objects.append(parse_object(lines_obj[start_ind:index]))
    # Return the list of dummy objects
    return objects


# :- Public functions used in the other classes


def read_sin(path: str | Path, only_chamber: bool = False,
             only_magnetron: bool = False) -> tuple[str, Chamber, Magnetron, list[DummyObject]] | Chamber | Magnetron:

    """
    Parses a simtra input file with the file ending ".sin" into a dictionary.

    :param path: path to the SIMTRA input file
    :param only_chamber: defines whether only the parameters for the sputtering chamber should be parsed
    :param only_magnetron: defines whether only the parameters for the magnetron should be parsed
    :return: the output path, chamber, magnetron and list of objects inside the sin file. If only_chamber is set to
    True, only the chamber is returned, the same goes for the magnetron
    """

    # Convert the path to a pathlib object if necessary
    path = Path(path) if isinstance(path, str) else path
    # Check for the correct file type
    if path.suffix != '.sin':
        raise ValueError('The given path needs to be a ".sin" file.')
    # Open the file
    with open(path) as file:
        # Read the file
        lines = file.readlines()
        # Get the output folder
        output_path = lines[0][30:].rstrip()
        # Get all environment condition parameters
        chamber = parse_chamber(lines)
        # If only the chamber should be parsed, return only the chamber
        if only_chamber:
            return chamber
        # Find the index of the sputtering source section
        source_index = lines.index('\'Source   ----------------------------------------\n') + 2
        # Get all parameters of the sputtering source
        magnetron = parse_magnetron(lines[source_index:])
        # If only the magnetron should be parsed, return here
        if only_magnetron:
            return magnetron
        # Get all parameters of the dummy objects
        objects = parse_dummy_objects(lines)
        # Return all objects
        return output_path, chamber, magnetron, objects


def read_smo(path: str | Path) -> Magnetron:

    """
    Parses a magnetron object file with the file ending ".smo" into a dictionary.

    :param path: path to the magnetron object file
    :return: Magnetron object
    """

    # Convert the path to a pathlib object if necessary
    path = Path(path) if isinstance(path, str) else path
    # Check for the correct file type
    if path.suffix != '.smo':
        raise ValueError('The given path needs to be a ".smo" file.')
    # Open the file and parse the parameters
    with open(path) as file:
        lines = file.readlines()
        return parse_magnetron(lines)


def read_sdo(path: str | Path) -> DummyObject:

    """
    Parses a dummy object file with the file ending ".sdo" into a Dummy Object.

    :param path: path to the dummy object file
    :return: Dummy Object
    """

    # Convert the path to a pathlib object if necessary
    path = Path(path) if isinstance(path, str) else path
    # Check for the correct file type
    if path.suffix != '.sdo':
        raise ValueError('The given path needs to be a ".sdo" file.')
    # Open the file and parse the parameters
    with open(path) as file:
        lines = file.readlines()
        return parse_object(lines)


def read_output_path_from_sin(path: str | Path) -> Path:

    """
    Also parses a SIMTRA ".sin" file, but only reads the output folder path

    :param path: path to the SIMTRA input file
    :return: output path defined in the input file
    """

    # Open the file and parse the parameters
    with open(path) as file:
        lines = file.readlines()
        # Get the output folder and return it
        return Path(lines[0][30:].rstrip())
