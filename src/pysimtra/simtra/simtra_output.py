from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Callable
import pandas as pd
import numpy as np

from ..simtra_read import read_output_path_from_sin


class SimtraOutput:

    """
    Class for handling the Simtra outputs.
    """

    metadata: dict[str, Any] | list[dict[str, Any]] = None
    n_particles: dict[str, np.ndarray] = None
    e_incidence: dict[str, np.ndarray] = None
    l_path: dict[str, np.ndarray] = None
    t_flight: dict[str, np.ndarray] = None
    n_collisions: dict[str, np.ndarray] = None
    ang_incidence: dict[str, np.ndarray] = None
    ang_scatter: dict[str, np.ndarray] = None

    def __init__(self, metadata: dict[str, Any] | list[dict[str, Any]], n_particles: dict[str, np.ndarray] = None,
                 e_incidence: dict[str, np.ndarray] = None, l_path: dict[str, np.ndarray] = None,
                 t_flight: dict[str, np.ndarray] = None, n_collisions: dict[str, np.ndarray] = None,
                 ang_incidence: dict[str, np.ndarray] = None, ang_scatter: dict[str, np.ndarray] = None):

        # Save all data inside the class
        self.metadata = {} if metadata is None else metadata
        self.n_particles = {} if n_particles is None else n_particles
        self.e_incidence = {} if e_incidence is None else e_incidence
        self.l_path = {} if l_path is None else l_path
        self.t_flight = {} if t_flight is None else t_flight
        self.n_collisions = {} if n_collisions is None else n_collisions
        self.ang_incidence = {} if ang_incidence is None else ang_incidence
        self.ang_scatter = {} if ang_scatter is None else ang_scatter

    @staticmethod
    def load_metadata(output_path: Path) -> dict[str, Any]:

        """
        Loads the metadata of the sputtering simulation, i.e. runtime and start time.

        :param output_path: path to the Simtra output
        :return: dictionary with all metadata of the simulation
        """

        # Create a dictionary with the simulation metadata
        metadata: dict[str, Any] = {}
        # Open the file
        with open(output_path / 'specificInformation.txt') as file:
            # Read the file
            lines = file.readlines()
            # Extract the number of days, hours, minutes, seconds and microseconds
            d, hms, mi = lines[1].rstrip().split(' : ')[1].split('.')
            h, m, s = hms.split(':')
            # Get the number of seconds from the string
            n_seconds = ((int(d) * 12 + int(h)) * 60 + int(m)) * 60 + int(s)
            metadata['simulation time [s]'] = n_seconds
            # Get the start time
            start_time = datetime.strptime(lines[3].rstrip().split(': ')[1], '%d/%m/%Y %H:%M:%S')
            metadata['start time'] = start_time
            # Calculate the finish time based on the start time and the simulation time
            metadata['finish time'] = start_time + timedelta(seconds=n_seconds)
            # Get the number of deposited particles
            metadata['number of particles'] = int(lines[4].rstrip().split(':\t')[1])
            # Return the metadata object
            return metadata

    @staticmethod
    def load_average_files(output_path: Path, f_name: str) -> dict[str, np.ndarray]:

        """
        Loads all averaged files with a given file name found in a Simtra output.

        :param output_path: path to the Simtra output
        :param f_name: file name to look for
        :return: dictionary of all found particle numbers
        """

        # Return the outputs as a dictionary since not every object will have saved deposition information
        outputs: dict[str, np.ndarray] = {}
        # Crawl through all directories and filter out the "N.txt" files
        for p in output_path.rglob('*'):
            if p.is_file() and p.name == f_name:
                # Get the name of the object
                name = p.parents[1].name
                # Load the file and extract the grid information
                outputs[name] = pd.read_csv(p, sep='\t', skiprows=1, header=None).to_numpy()
        # Return the outputs
        return outputs

    @classmethod
    def from_file(cls, file_path: Path | str):

        """
        Creates a SimtraOutput object from a Simtra input file at a given path.

        :param file_path: path to the Simtra input file used to run the simulation
        :return: SimtraOutput object
        """

        # Convert the path from string if necessary
        file_path = Path(file_path) if isinstance(file_path, str) else file_path
        # Load the output file path from the Simtra input file
        output_path = read_output_path_from_sin(file_path)
        # Load the metadata from the path
        mdata = cls.load_metadata(output_path)
        # Load all averaged simulation results
        n_parts = cls.load_average_files(output_path, 'N.txt')
        e_inc = cls.load_average_files(output_path, 'E.txt')
        l_path = cls.load_average_files(output_path, 'Path.txt') 
        t_flight = cls.load_average_files(output_path, 'Fligth.txt') 
        n_coll = cls.load_average_files(output_path, 'NColl.txt')
        ang_inc = cls.load_average_files(output_path, 'Ksi.txt')
        ang_scat = cls.load_average_files(output_path, 'ScatAngle.txt')
        # Create the Simtra output
        return cls(mdata, n_parts, e_inc, l_path, t_flight, n_coll, ang_inc, ang_scat)

    @staticmethod
    def merge(d1: dict, d2: dict, op: Callable) -> dict:

        """
        Merges two dictionaries by combining all values of keys which are in both dictionaries with the specified
        operator and just transfers the ones only occurring once.

        :param d1: dictionary 1
        :param d2: dictionary 2
        :param op: operator which combines the values
        :return: merged dictionary
        """

        # Add all key/value pairs to the first dict if not already, otherwise add both values together
        for key in d2.keys():
            d1[key] = op([d1[key], d2[key]], axis=0) if key in d1.keys() else d2[key]
        # Return the first dictionary
        return d1

    def merge_outputs(self, output1, output2) -> object:

        """
        Merges two SimtraOutput objects. The metadata is appended, the rest of the data is either combined by addition
        or by calculating the average.

        :param output1: SimtraOutput object 1
        :param output2: SimtraOutput object 2
        :return: merged SimtraOutput object
        """

        # Add both metadata dictionaries together. If one of them is a list already, the object already holds at
        # least two simulation results
        mdata1 = [output1.metadata] if isinstance(output1.metadata, dict) else output1.metadata
        mdata2 = [output2.metadata] if isinstance(output2.metadata, dict) else output2.metadata
        mdata = mdata1 + mdata2
        # Add the other results together depending on the type: either calculate average or the sum
        n_parts = self.merge(output1.n_particles, output2.n_particles, op=np.sum)
        e_inc = self.merge(output1.e_incidence, output2.e_incidence, op=np.mean)
        l_path = self.merge(output1.l_path, output2.l_path, op=np.mean)
        t_flight = self.merge(output1.t_flight, output2.t_flight, op=np.mean)
        n_coll = self.merge(output1.n_collisions, output2.n_collisions, op=np.mean)
        ang_inc = self.merge(output1.ang_incidence, output2.ang_incidence, op=np.mean)
        ang_scat = self.merge(output1.ang_scatter, output2.ang_scatter, op=np.mean)
        # Create a new class with the combined data
        return SimtraOutput(mdata, n_parts, e_inc, l_path, t_flight, n_coll, ang_inc, ang_scat)

    def __add__(self, other):

        """
        Manages the addition of two SimtraOutput objects. The metadata is appended, the rest of the data is either
        combined by addition or by calculating the average.

        :param other: second object to add to this class
        :return: SimtraOutput object with all data combined
        """

        # Check if the second object is a Simtra output object too
        if isinstance(other, SimtraOutput):
            return self.merge_outputs(self, other)
        # For making the sum() function work, also addition with 0 is needed
        elif isinstance(other, int):
            return self
        # In any other case, return an error
        return NotImplemented

    def __radd__(self, other):

        """
        Manages the reverse addition of two SimtraOutput objects. The metadata is appended, the rest of the data is
        either combined by addition or by calculating the average. Overriding this function is needed for making the
        "sum()" function work since it always starts by adding 0 to the addition. See this for further information:
        https://stackoverflow.com/questions/5082190/typeerror-after-overriding-the-add-method

        :param other: second object to add to this class
        :return: SimtraOutput object with all data combined
        """

        # Check if the second object is a Simtra output object too
        if isinstance(other, SimtraOutput):
            return self.merge_outputs(self, other)
        # In order to use the sum() function, also implement handling of addition with 0
        elif isinstance(other, int):
            return self
        # In any other case, return an error
        return NotImplemented
