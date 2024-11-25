from pathlib import Path

from ..surfaces import Surface


class DummyObject:

    """
    Class for describing a SIMTRA dummy object.
    """

    # Parameters defining the object
    name: str = None
    surfaces: list[Surface] = None
    position: tuple = None  # (x, y, z) in m
    orientation: tuple = None  # (phi, theta, psi) in °

    def __init__(self, name: str, surfaces: list[Surface],  position: tuple = (0, 0, 0),
                 orientation: tuple = (0, 0, 0)):

        """
        :param name: name of the dummy object
        :param surfaces: list of Surface objects which make up the dummy object
        :param position: position (x, y, z) in m
        :param orientation: orientation (phi, theta, psi) in °
        """

        # Store the parameters in the class
        self.name = name
        self.surfaces = surfaces
        self.position = position
        self.orientation = orientation

    @classmethod
    def from_file(cls, path: Path | str):

        """
        Creates a dummy object from a given ".sdo" file.

        :param path: path to the dummy object file with ending ".sdo"
        :return: dummy Object
        """

        # Import the method here to avoid circular imports
        from ..simtra_read import read_sdo
        # Convert the string to a path if necessary
        path = Path(path) if isinstance(path, str) else path
        # Load the file
        return read_sdo(path)

    # :- Magic functions

    def __eq__(self, other) -> bool:

        # Check if the second object is a dummy object too
        if isinstance(other, DummyObject):
            # Check if the parameters of both classes are identical
            return vars(self) == vars(other)
        # In any other case, return an error
        return NotImplemented

    # :- Conversion functions

    def to_sdo(self, path: str | Path) -> None:

        """
        Stores the dummy object as a simtra dummy object file (with file ending ".sdo").

        :param path: path at which the simtra magnetron object ".sdo" should be stored
        :return:
        """

        # Import the method here to avoid circular imports
        from ..simtra_write import write_sdo
        # Convert the string to a path if necessary
        path = Path(path) if isinstance(path, str) else path
        # Check if the file ending is ".sdo" and throw an error if otherwise
        if path.suffix != '.sdo':
            ValueError('The given path does not have the ".sdo" file extension.')
        # Save the smo file
        write_sdo(self, path)
