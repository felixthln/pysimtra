import numpy as np


# :- Elementary rotation matrices


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


# :- Orientation of a surface or an object


def rotation_matrix(orientation: tuple) -> np.ndarray:

    """
    Calculates the rotation matrix belonging to a set of Euler angles. SIMTRA uses the ZYZ convention and stores the
    three angles in the order (phi, theta, psi), where phi is the OUTER rotation, i.e. the one applied last. The
    rotation is therefore composed as R_z(phi) @ R_y(theta) @ R_z(psi). This function is the single definition of that
    convention, "calc_angles" in "simtra_read.py" inverts it.

    The order matters for the object orientations in particular: unlike a surface, whose orientation is converted into
    basis vectors before it is written, an object orientation is written into the input file as the three angles
    themselves and is therefore interpreted by SIMTRA rather than by this package. A magnetron sitting at the azimuth
    alpha of an anker circle and leaning towards the chamber axis needs R_z(alpha) @ R_y(-tilt), so the azimuth has to
    end up in phi. Putting it into psi instead tilts every magnetron towards -x regardless of where it sits.

    :param orientation: orientation (phi, theta, psi) in °
    :return: 3x3 rotation matrix converting from the local into the surrounding coordinate system
    """

    # Extract the three angles
    phi, theta, psi = orientation
    # Compose the rotation and round it to E-15 to suppress the numerical noise of the matrix products
    return np.around(R_z(phi) @ R_y(theta) @ R_z(psi), decimals=15)


def local_basis(orientation: tuple) -> np.ndarray:

    """
    Calculates the basis vectors a, b and c of a surface or an object with a given orientation. SIMTRA describes every
    surface by these three vectors rather than by the angles themselves.

    :param orientation: orientation (phi, theta, psi) in °
    :return: 3x3 matrix holding the basis vectors a, b and c as its rows
    """

    # Rotate the unit vectors of the local coordinate system
    rot_mat = rotation_matrix(orientation)
    a = rot_mat.dot([1, 0, 0])
    b = rot_mat.dot([0, 1, 0])
    # The third vector completes the right-handed system
    return np.vstack((a, b, np.cross(a, b)))