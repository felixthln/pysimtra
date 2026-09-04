from __future__ import annotations

import os
from sys import platform
from pathlib import Path
from multiprocessing import Pool
from itertools import repeat
from typing import NamedTuple
import subprocess

from .simtra_output import SimtraOutput
from ..simtra_read import read_output_path_from_sin


class SimtraRun(NamedTuple):

    """
    Result of a single SIMTRA subprocess call, holding everything needed to tell whether the run succeeded and, if it
    did not, what SIMTRA printed to the console before giving up.
    """

    # Path of the ".sin" file which was passed to SIMTRA
    input_file: Path
    # Exit code of the "simtra_cmd.exe" process
    return_code: int
    # Everything the process wrote to stdout and stderr, in the order it was written
    console_output: str

    def __str__(self) -> str:
        # Show the file name, the exit code and the indented console output, so several runs stay distinguishable
        text = self.console_output.strip()
        text = '\n'.join('    ' + line for line in text.splitlines()) if text else '    <no console output>'
        return '%s (exit code %d):\n%s' % (self.input_file.name, self.return_code, text)


class SimtraError(RuntimeError):

    """
    Raised when one or more SIMTRA runs did not produce a usable result. The console output of the failed runs is part
    of the error message, and the runs themselves are available via the "runs" attribute.
    """

    def __init__(self, runs: list[SimtraRun], message: str = None):
        # Store the failed runs, so they can be inspected programmatically instead of being parsed out of the message
        self.runs = runs
        # Build the message from the console output of every failed run
        message = 'SIMTRA failed on %d of the simulation input files.' % len(runs) if message is None else message
        super().__init__(message + '\n\n' + '\n\n'.join(str(run) for run in runs))


def run_sim(inp_path: Path, exe_path: Path, verbose: bool = False) -> SimtraRun:

    """
    Runs a single SIMTRA simulation as a subprocess and collects everything the executable prints. As SIMTRA writes its
    progress and its error messages to the console only, this output is the sole source of information when a
    simulation input file is rejected.

    :param inp_path: path to the SIMTRA input file
    :param exe_path: path to the SIMTRA command line executable
    :param verbose: if True, the console output is printed line by line while the simulation is running, prefixed with
        the name of the input file so that parallel runs stay distinguishable
    :return: SimtraRun object holding the input file, the exit code and the console output
    """

    # Collect the output line by line instead of using "subprocess.run", so it can be shown while SIMTRA is still
    # running instead of only after it has finished
    lines: list[str] = []
    # Redirect the error stream into the output stream, since SIMTRA mixes both and the interleaving matters
    process = subprocess.Popen([str(exe_path), '-i', str(inp_path)], stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, text=True, bufsize=1)
    # Prefix every line with the name of the input file, as the lines of all parallel runs end up in the same console
    prefix = '[%s] ' % inp_path.stem
    # Read the output until the process closes the stream
    for line in process.stdout:
        lines.append(line)
        if verbose:
            print(prefix + line.rstrip(), flush=True)
    # Wait for the process to terminate to get its exit code
    process.wait()
    return SimtraRun(inp_path, process.returncode, ''.join(lines))


class SimtraSimulation:

    """
    Class for running one or multiple SIMTRA simulations.
    """

    def __init__(self, exe_path: Path | str = None):
        # If no path is provided, use the standard one
        if exe_path is None:
            exe_path = Path(__file__).parent / Path('app/simtra_cmd.exe')
        # If the exe path is a string, convert it to a pathlib.Path object
        exe_path = Path(exe_path) if isinstance(exe_path, str) else exe_path
        # Check if the SIMTRA command file is there
        if not exe_path.exists():
            raise ValueError('The "simtra_cmd.exe" was not found. Use "import_exe" method to it')
        self._exe_path = exe_path
        # Console output of the runs of the last "run" call, kept for troubleshooting successful but suspicious runs
        self.runs: list[SimtraRun] = []

    @staticmethod
    def _check_run(run: SimtraRun) -> bool:

        """
        Checks whether a single SIMTRA run produced a usable result. Beside the exit code, the output directory is
        checked as well, because SIMTRA reports a faulty input file on the console and still terminates normally.

        :param run: run to check
        :return: True if the run succeeded, False otherwise
        """

        # A non-zero exit code always means the run failed
        if run.return_code != 0:
            return False
        # Otherwise, check whether the results were actually written to the output directory given in the input file
        try:
            output_path = read_output_path_from_sin(run.input_file)
        except (OSError, ValueError, IndexError):
            # The input file itself could not be read back, so there is nothing to look for
            return False
        # SIMTRA writes this file at the end of every successful simulation
        return (output_path / 'specificInformation.txt').exists()

    def run(self, simtra_files: Path | list[Path], delete_input_files: bool = False,
            verbose: bool = False) -> SimtraOutput | list[SimtraOutput]:

        """
        Runs SIMTRA on the provided simulation input files. The command line version of SIMTRA is used for that, that's
        why this code can only be executed on Windows.

        :param simtra_files: list of simtra files to simulate
        :param delete_input_files: determines whether the input files will be deleted after the simulation. Input files
            of failed runs are always kept, so that they can be inspected
        :param verbose: if True, the console output of SIMTRA is printed while the simulations are running
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
            runs = pool.starmap(run_sim, zip(sim_files, repeat(self._exe_path), repeat(verbose)))
        # Keep the runs, so the console output of a simulation which finished but looks wrong can still be read out
        self.runs = runs
        # Collect all runs that either returned an error code or did not write any results
        failed = [run for run in runs if not self._check_run(run)]
        # If any of them failed, raise an error containing the console output of SIMTRA and keep all input files
        if failed:
            raise SimtraError(failed)
        # Load the results and wrap them in the output class
        outputs = [SimtraOutput.from_file(file) for file in sim_files]
        # When the simulation is complete, remove the input files if desired
        if delete_input_files:
            for file in sim_files:
                os.remove(file)
        # Return the outputs either as a list or as a single output object
        return outputs[0] if isinstance(simtra_files, Path) else outputs
