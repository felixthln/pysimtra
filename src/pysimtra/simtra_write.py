import numpy as np
from pathlib import Path

from .surfaces import Surface, Plane, Circle, Rectangle, Cylinder, Cone, Sphere
from .components import Chamber, Magnetron, DummyObject


# :- Private supporting functions


# Function to write a single key/value pair to a text file
def write(key: str, value, file, unit: str = None):
    # Convert the value to a string and add the key with a fixed length of 30 characters
    string = '{:<30}'.format(key) + str(value)
    # Add a unit if specified
    if unit is not None:
        string += ' (%s)' % unit
    # Write the string to the file
    file.write(string + '\n')


# Function to save all chamber parameters
def write_chamber(ch: Chamber, file):
    # Insert the spacer for the chamber parameters
    file.write('\'chamber   ---------------------------------------\n\n')
    # Add the type of the chamber
    file.write('{:<30}'.format('shapeChamber') + ch.shape + '\n')
    # Convert the chamber shape parameters into a list of parameters
    params = [ch.radius, ch.length] if ch.shape == 'cylinder' else [ch.height, ch.width, ch.length]
    # Add the chamber shape
    file.write('{:<30}'.format('') + ' '.join('%g' % p for p in params) + ' (m)\n')
    # Add the chamber temperature and pressure as well as the process gas
    write('temperature', ch.temperature, file, unit='K')
    write('pressure', ch.pressure, file, unit='Pa')
    write('gasElement', ch.gas_element, file)
    # Add the seed number
    write('seed', ch.seed_number, file)
    # Save the chamber walls grid
    file.write('{:<30}'.format('chamberWallsGrid') + ' '.join('%g' % c for c in ch.chamber_walls_grid) + '\n')
    # Save the indices of deposition walls for which deposition info should be saved
    file.write('{:<30}'.format('saveDepositionWall') + ' '.join('%g' % s for s in ch.save_deposition_walls) + '\n')
    # If the individual particle data should be saved, add the parameter
    if ch.save_individual_data:
        file.write('saveIndividualData\n')
    # Add the spacer to end this section
    file.write('\'-------------------------------------------------\n\n')


# Generate a rotation matrix around z
def R_z(angle: float) -> np.ndarray:
    # Convert the angle from degrees in radians
    angle = angle / 180 * np.pi
    # Return the z rotation matrix
    return np.array([[np.cos(angle), -np.sin(angle), 0], [np.sin(angle), np.cos(angle), 0], [0, 0, 1]])


# Generate a rotation matrix around y
def R_y(angle: float) -> np.ndarray:
    # Convert the angle from degrees in radians
    angle = angle / 180 * np.pi
    # Return the y rotation matrix
    return np.array([[np.cos(angle), 0, np.sin(angle)], [0, 1, 0], [-np.sin(angle), 0, np.cos(angle)]])


# Calculate the rotation matrix of a surface
def calc_R(sur: Surface) -> np.ndarray:
    # Extract the angles from the dictionary
    phi, theta, psi = sur.orientation
    # Calculate the rotation matrix for the zyz convention
    rot_mat = R_z(psi) @ R_y(theta) @ R_z(phi)
    # Round the rotation matrix to E-15
    rot_mat = np.around(rot_mat, decimals=15)
    # Calculate a, b and c
    a = rot_mat.dot([1, 0, 0])
    b = rot_mat.dot([0, 1, 0])
    c = np.cross(a, b)
    # The first row of the rotation matrix corresponds to the position
    r1 = np.array(sur.position)
    # The second and third also need to hold the individual surface parameters depending on the type
    # In case of a perforated plane, add the outer parameters
    if isinstance(sur, Plane) and sur.perforation_type is not None:
        r2, r3 = r1 + sur.outer_param_1 * a, r1 + sur.outer_param_2 * b
    # In case of a non-perforated circle, only use the outer radius
    elif isinstance(sur, Plane) and sur.plane_type == 'circle':
        r2, r3 = r1 + sur.outer_param_1 * a, r1 + sur.outer_param_1 * b
    # In case the surface type is a rectangle, use the outer width and height
    elif isinstance(sur, Plane) and sur.plane_type == 'rectangle':
        r2, r3 = r1 + sur.outer_param_1 * a, r1 + sur.outer_param_2 * b
    # If the surface type is a cylinder
    elif isinstance(sur, Cylinder):
        r2, r3 = r1 + sur.height * c, r1 + sur.radius * a
    # If the surface type is a cone
    elif isinstance(sur, Cone):
        r2, r3 = r1 + sur.height * c, r1 + sur.height * c + sur.big_rho * a
    # If the surface type is a sphere
    elif isinstance(sur, Sphere):
        r2, r3 = r1 + sur.radius * c, r1 + sur.radius * a
    else:
        raise ValueError('Surface type could not be identified.')
    # Combine the three rows and return the matrix
    return np.vstack((r1, r2, r3))


# Function to save the parameters of a simtra surface to the simtra input file
def write_surface(sur: Surface, file):
    # First store the type and name of the object
    file.write('{:<30}'.format(sur.simtra_type) + sur.name + '\n')
    # Calculate the rotation matrix of the surface
    R = calc_R(sur)
    # Safe the rotation matrix
    file.write(' '.join('%g' % s for s in np.ravel(R[0])) + '\n')
    file.write(' '.join('%g' % s for s in np.ravel(R[1])) + '\n')
    file.write(' '.join('%g' % s for s in np.ravel(R[2])) + '\n')
    # Add the shape dependent parameters
    if isinstance(sur, Circle) or isinstance(sur, Rectangle) or isinstance(sur, Plane):
        # Store the type of the planepiece
        p1 = 1 if sur.plane_type == 'rectangle' else 2
        # Store whether (and by what) the planepiece is perforated
        p2 = 0 if sur.perforation_type is None else 1 if sur.perforation_type == 'rectangle' else 2
        # Store the shape dependent parameters of the outer shape
        p3, p4 = sur.outer_param_1, sur.outer_param_2
        # Store the shape dependent parameters of the inner shape
        p5 = 0 if sur.perforation_type is None else sur.inner_param_1
        p6 = 0 if sur.perforation_type is None else sur.inner_param_2
        # Write the parameters to the file
        file.write(' '.join('%g' % s for s in [p1, p2, p3, p4, p5, p6]) + '\n')
    elif isinstance(sur, Cylinder):
        # Store the opening angle
        file.write('%g' % sur.dtheta + '\n')
    elif isinstance(sur, Cone):
        # Store the small radius and the opening angle
        file.write(' '.join('%g' % s for s in [sur.small_rho, sur.dtheta]) + '\n')
    elif isinstance(sur, Sphere):
        # Store the two opening angles
        file.write(' '.join('%g' % s for s in [sur.dphi, sur.dtheta]) + '\n')
    # Store whether depositions on the surface should be saved
    if sur.save_avg_data:
        # Change the prefix depending on whether the data should be saved double
        ind = '3' if sur.save_ind_data else '1'
        file.write(ind + ' ' + ' '.join(str(s) for s in sur.avg_grid) + ' N E NColl\n')
    elif sur.save_ind_data:
        file.write('2\n')
    # If no data should be saved, add a zero
    else:
        file.write('0\n')
    # Add a newline character at the end to separate the surfaces
    file.write('\n')


# Function to save the parameters of a simtra object
def write_object(obj: DummyObject, _type: str, file):
    # First store the type and name of the object
    file.write('{:<30}'.format(_type) + obj.name + ' {\n')
    # Store the global position and orientation of the object
    file.write('{:<30}'.format('position') + ' '.join('%g' % s for s in obj.position) + '\n')
    file.write('{:<30}'.format('orientation') + ' '.join('%g' % s for s in obj.orientation) + '\n')
    # It seems like the shape is left blank all the time
    file.write('shape\n0\n')
    # Store the surfaces of the object
    for surface in obj.surfaces:
        write_surface(surface, file)
    # Add a closing bracket to indicate the end of the object definition
    file.write('}\n\n')


def write_magnetron(mag: Magnetron, file):
    # Store the transported element
    write('transportedElement', mag.transported_element, file)
    # Store the potential
    write('potential', mag.interaction_potential, file)
    # Depending on the potential, add either the scattering table or the screening function
    if mag.interaction_potential == 'specified':
        write('scatteringTable', mag.scattering_table_path, file)
    elif mag.interaction_potential == 'screenedCoulomb':
        write('screeningFunction', mag.screening_function, file)
    # Save whether gas motion and diffusion should be taken into accound
    write('withGasMotion', 'yes' if mag.with_gas_motion else 'no', file)
    write('goToDiffusion', 'yes' if mag.go_to_diffusion else 'no', file)
    # Define the source type
    write('sourceType', mag.source_type, file)
    # Save the number of particles and after how many particles the results should be saved
    write('numberOfParticles', str(mag.n_particles) + ' ' + str(mag.save_every_n_particles), file)
    # Save how the energy distribution should be calculated
    write('energyDistribution', mag.energy_distribution, file)
    # Save the surface binding energy
    write('surfBindEnergy', mag.surface_binding_energy, file, 'eV')
    # Depending on the energy distribution, store either the maximum ion energy or the information about the SRIM file
    if mag.energy_distribution == 'Thompson':
        write('maxIonEnergy', mag.max_ion_energy, file, 'eV')
    elif mag.energy_distribution == 'SRIM':
        write('SRIMType', mag.srim_type, file)
        write('SRIMFile', mag.srim_file_path, file)
    # Store the type of angular distribution
    write('angularDistribution', mag.angular_distribution, file)
    # If the angular distribution is defined by a user defined cosine distribution, store the coefficients
    if mag.angular_distribution == 'User':
        file.write('{:<30}'.format('c_i') + ' '.join('%g' % c for c in mag.cosine_coefficients) + '\n')
    # Store the parameters of the magnetron object
    write_object(mag.m_object, 'magnetronObject', file)
    # At the end of the magnetron object definition, add information about the sputtering surface
    write('surfaceSputters', mag.sputter_surface_index, file)
    write('racetrack_t0', mag.racetrack_t0, file)  # whatever this is
    write('fileRacetrack', str(mag.racetrack_file_path), file)  # make sure the path is converted to string
    write('racetrackType', mag.racetrack_type, file)


# Function to save a dummy object
def write_dummy_objects(objects: list[DummyObject], file):
    # Insert a spacer for the objects
    file.write('\'objects   ---------------------------------------\n\n')
    # Store the dummy objects
    for obj in objects:
        write_object(obj, 'object', file)
    # Lastly, insert the bottom spacer
    file.write('\'-------------------------------------------------\n\n')


# Function to save movement information (not yet fully implemented)
def write_movement_info(file):
    # Insert a spacer
    file.write('\'movement   --------------------------------------\n\n')
    # Add code here

    # Insert the bottom spacer
    file.write('\'-------------------------------------------------\n')


# :- Public functions used in the other classes


def write_sin(output_path: str | Path, chamber: Chamber, magnetron: Magnetron, objects: list[DummyObject],
              path: str | Path) -> None:

    """
    Saves a sputter system as a simtra input file.

    :param output_path: output path of the simulation
    :param chamber: chamber object
    :param magnetron: magnetron object
    :param objects: list of dummy objects
    :param path: path to save the .sin file to
    :return:
    """

    # Convert the path to a pathlib object if necessary
    path = Path(path) if isinstance(path, str) else path
    # Check if the file ending is ".sin" and throw an error if otherwise
    if path.suffix != '.sin':
        ValueError('The given path does not have the ".sin" file extension.')
    with open(path, 'w') as file:
        # Write the output path
        write('outputfolder', output_path, file)
        # Store the chamber parameters
        write_chamber(chamber, file)
        # Insert the spacer for the source parameters
        file.write('\'Source   ----------------------------------------\n\n')
        # Store the source parameters
        write_magnetron(magnetron, file)
        # Lastly, insert the spacer
        file.write('\n\n\'-------------------------------------------------\n\n')
        # Store the dummy objects
        write_dummy_objects(objects, file)
        # Store the movement information
        write_movement_info(file)


def write_smo(mag: Magnetron, path: str | Path) -> None:

    """
    Saves a magnetron given by a dictionary of parameters into a text file.

    :param mag: magnetron object to create a .smo file from
    :param path: path at which the file should be saved
    :return:
    """

    # Convert the path to a pathlib object if necessary
    path = Path(path) if isinstance(path, str) else path
    # Check if the file ending is ".smo" and throw an error if otherwise
    if path.suffix != '.smo':
        ValueError('The given path does not have the ".smo" file extension.')
    with open(path, 'w') as file:
        # Write the source parameters
        write_magnetron(mag, file)


def write_sdo(dummy_object: DummyObject, path: str | Path) -> None:

    """
    Saves a dummy object given by a dictionary of parameters into a text file.

    :param dummy_object: dummy object to create a .sdo file from
    :param path: path at which the file should be saved
    :return:
    """

    # Convert the path to a pathlib object if necessary
    path = Path(path) if isinstance(path, str) else path
    # Check if the file ending is ".sdo" and throw an error if otherwise
    if path.suffix != '.sdo':
        ValueError('The given path does not have the ".sdo" file extension.')
    with open(path, 'w') as file:
        # Write the dummy object parameters
        write_object(dummy_object, 'object', file)
