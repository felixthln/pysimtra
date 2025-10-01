from pathlib import Path
import shutil

# Import the surfaces and components
from .surfaces import Circle, Rectangle, Cylinder, Cone, Sphere
from .components import Chamber, Magnetron, DummyObject
# Import the sputter system class
from .sputter_system import SputterSystem
# Import the SIMTRA simulation class
from .simtra import SimtraSimulation
# Import the SimtraOutput class
from .simtra import SimtraOutput
# Import the functions for reading and writing SIMTRA files
from .simtra_read import read_sin, read_smo, read_sdo
from .simtra_write import write_sin, write_smo, write_sdo


# Method to import the SIMTRA executable
def import_exe(path: Path | str):

    """
    Imports the SIMTRA executable into the package.

    :param path: path to the SIMTRA directory containing the "simtra_cmd.exe" as well as the "ScatteringAngleTables"
        directory
    :return:
    """

    # Convert the string to a path if necessary
    path = Path(path) if isinstance(path, str) else path
    # Make sure the path is a directory
    if not path.is_dir():
        raise ValueError('The given path "%s" is not a directory.' % str(path))
    # Make sure the path has the command line version of SIMTRA as well as the scattering angle tables
    if not (path / 'simtra_cmd.exe').exists():
        raise ValueError('The "simtra_cmd.exe" could\'nt be found in the given directory.')
    if not (path / 'ScatteringAngleTables').is_dir():
        raise ValueError('The "ScatteringAngleTables" directory could\'nt be found in the given directory.')
    # Create a directory inside the package to store the executable
    dest_path = Path(__file__).parent / 'simtra' / 'app'
    dest_path.mkdir(parents=True, exist_ok=True)
    # Copy the SIMTRA command version, replace if already exists
    shutil.copy(path / 'simtra_cmd.exe', dest_path / 'simtra_cmd.exe', )
    # Copy all contents of the scattering angle table, replace if already exists
    shutil.copytree(path / 'ScatteringAngleTables', dest_path / 'ScatteringAngleTables', dirs_exist_ok=True)
    # Also create a directory for storing the temporary SIMTRA files
    temp_path = Path(__file__).parent / 'temporary'
    temp_path.mkdir(parents=True, exist_ok=True)
