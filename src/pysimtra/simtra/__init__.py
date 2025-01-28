import os
from sys import platform
from pathlib import Path
from multiprocessing import Pool
from itertools import repeat
import subprocess

from .simtra_output import SimtraOutput


def run_sim(inp_path: Path, exe_path: Path) -> str:

    """
    Runs a single SIMTRA simulation as a subprocess.

    :param exe_path: path to the SIMTRA command line executable
    :param inp_path: path to the SIMTRA input file
    :return: output of the SIMTRA code as a string
    """

    output = subprocess.run([exe_path, '-i', inp_path], capture_output=True, text=True)
    return str(output)


class SimtraSimulation:

    """
    Class for running one or multiple SIMTRA simulations.
    """

    # Path to the simtra executable which actually handles the simulation
    _exe_path: Path = None

    def __init__(self, exe_path: Path | str = None):
        # If no path is provided, use the standard one
        if exe_path is None:
            exe_path = Path(__file__).parent / Path('app/simtra_cmd.exe')
        # Check if the SIMTRA command file is there
        if not exe_path.exists():
            raise ValueError('The "simtra_cmd.exe" was not found. Use "import_exe" method to it')
        # If the exe path is a string, convert it to a pathlib.Path object
        self._exe_path = Path(exe_path) if isinstance(exe_path, str) else exe_path

    def run(self, simtra_files: Path | list[Path],
            delete_input_files: bool = False) -> SimtraOutput | list[SimtraOutput]:

        """
        Runs SIMTRA on the provided simulation input files. The command line version of SIMTRA is used for that, that's
        why this code can only be executed on Windows.

        :param simtra_files: list of simtra files to simulate
        :param delete_input_files: determines whether the input files will be deleted after the simulation
        :return: SIMTRA output or a list of SIMTRA outputs depending on how many SIMTRA input files were passed to the
        function
        """

        # Check the platform, and raise an error if it is not Windows
        if platform != 'win32':
            raise OSError('As SIMTRA is based on the .NET platform, this code only works on Windows.')
        # Handle when only one input file was passed to the function
        sim_files = [simtra_files] if isinstance(simtra_files, Path) else simtra_files
        # Perform the simulations on different threads managed by a pool
        with Pool() as pool:
            notes = pool.starmap(run_sim, zip(sim_files, repeat(self._exe_path)))
        # Load the results and wrap them in the output class
        outputs = [SimtraOutput.from_file(file) for file in sim_files]
        # When the simulation is complete, remove the input files if desired
        if delete_input_files:
            for file in sim_files:
                os.remove(file)
        # Return the outputs either as a list or as a single output object
        return outputs[0] if isinstance(simtra_files, Path) else outputs
