from pathlib import Path
import warnings
from datetime import timedelta  # datetime,
from dateutil import parser
from typing import Any, Callable
import pandas as pd
import numpy as np

from ..simtra_read import read_output_path_from_sin, read_magnetron_name_from_sin


# Type of the averaged results: object name -> surface name -> averaged grid
AvgData = dict[str, dict[str, np.ndarray]]


class SimtraOutput:

    """
    Class for handling the Simtra outputs. All averaged results are stored as nested dictionaries, keyed first by the
    name of the object and second by the name of the surface, e.g. "n_particles['substrate']['grid']". Only surfaces
    with the "save_avg_data" attribute appear. The magnetron launching the particles is stored under its own name like
    any other object; note that the particles counted on its sputtering surface are the redeposited ones. The chamber
    walls are stored under the name in "CHAMBER", with the walls as surfaces: "mantle", "zmin" and "zmax" for a
    cylindrical chamber and "xmin", "xmax", "ymin", "ymax", "zmin" and "zmax" for a cuboid one.
    """

    # Name under which the chamber walls are stored next to the objects
    CHAMBER = 'chamber'

    def __init__(self, metadata: dict[str, Any] | list[dict[str, Any]], source: str | None = None,
                 n_particles: AvgData = None, e_incidence: AvgData = None, l_path: AvgData = None,
                 t_flight: AvgData = None, n_collisions: AvgData = None, ang_incidence: AvgData = None,
                 ang_scatter: AvgData = None):

        """
        :param metadata: metadata of the simulation, or a list of those if multiple simulations were combined
        :param source: name of the magnetron which launched the particles
        :param n_particles: number of arriving particles per object and surface
        :param e_incidence: average energy of the arriving particles per object and surface
        :param l_path: average path length of the arriving particles per object and surface
        :param t_flight: average time of flight of the arriving particles per object and surface
        :param n_collisions: average number of collisions of the arriving particles per object and surface
        :param ang_incidence: average angle of incidence of the arriving particles per object and surface
        :param ang_scatter: average scattering angle of the arriving particles per object and surface
        """

        # Save all data inside the class
        self.metadata: dict[str, Any] | list[dict[str, Any]] = {} if metadata is None else metadata
        self.source: str | None = source
        self.n_particles: AvgData = {} if n_particles is None else n_particles
        self.e_incidence: AvgData = {} if e_incidence is None else e_incidence
        self.l_path: AvgData = {} if l_path is None else l_path
        self.t_flight: AvgData = {} if t_flight is None else t_flight
        self.n_collisions: AvgData = {} if n_collisions is None else n_collisions
        self.ang_incidence: AvgData = {} if ang_incidence is None else ang_incidence
        self.ang_scatter: AvgData = {} if ang_scatter is None else ang_scatter

    @staticmethod
    def load_metadata(output_path: Path) -> dict[str, Any]:

        """
        Loads the metadata of the sputtering simulation: the simulation time, the start and finish time and the number
        of particles redeposited on the target.

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
            n_seconds = ((int(d) * 24 + int(h)) * 60 + int(m)) * 60 + int(s)
            metadata['simulation time [s]'] = n_seconds
            # Get the start time
            start_time = parser.parse(lines[3].rstrip().split(': ')[1])
            #start_time = datetime.strptime(lines[3].rstrip().split(': ')[1], '%d/%m/%Y %H:%M:%S')
            metadata['start time'] = start_time
            # Calculate the finish time based on the start time and the simulation time
            metadata['finish time'] = start_time + timedelta(seconds=n_seconds)
            # Get the number of particles which were redeposited on the target. SIMTRA writes no other particle
            # number into this file; the number of launched particles is in the header of every "N.txt" instead
            metadata['redeposited particles'] = int(lines[4].rstrip().split(':\t')[1])
            # Return the metadata object
            return metadata

    @staticmethod
    def load_average_files(output_path: Path, f_name: str, mag_name: str) -> AvgData:

        """
        Loads all averaged files with a given file name found in a Simtra output. SIMTRA stores the files of the dummy
        objects as "depositionDummyObjects/<object>/<surface>/<f_name>", but the ones of the magnetron launching the
        particles as "depositionMagnetron/<surface>/<f_name>", i.e. without the name of the magnetron. The chamber walls
        are stored as "depositionChamber/<wall>/<f_name>" and are filed under the name in "CHAMBER". Each wall's grid
        consists of the two numbers of the chamber's averaging grid lying in the plane of the wall, e.g. (theta, z)
        for the mantle of a cylinder or (y, z) for the x-walls of a cuboid.

        :param output_path: path to the Simtra output
        :param f_name: file name to look for
        :param mag_name: name of the magnetron which launched the particles, used as its key in the dictionary
        :return: nested dictionary of all found files, keyed by object name and surface name
        """

        # Return the outputs as a dictionary since not every object will have saved deposition information
        outputs: AvgData = {}
        # Collect the files of the dummy objects, sorted to make the order of the dictionary reproducible
        files = [(p.parents[1].name, p) for p in sorted((output_path / 'depositionDummyObjects').glob('*/*/' + f_name))]
        # Add the files of the magnetron, which lack the object directory
        files += [(mag_name, p) for p in sorted((output_path / 'depositionMagnetron').glob('*/' + f_name))]
        # An object with the name of the chamber would get its surfaces mixed up with the chamber walls
        if any(obj_name == SimtraOutput.CHAMBER for obj_name, _ in files):
            warnings.warn('An object is named "%s", its surfaces are stored together with the chamber walls.'
                          % SimtraOutput.CHAMBER)
        # Add the files of the chamber walls, which lack an object directory as well
        files += [(SimtraOutput.CHAMBER, p) for p in sorted((output_path / 'depositionChamber').glob('*/' + f_name))]
        # Load each file into the dictionary of its object, with the directory name being the surface name
        for obj_name, p in files:
            outputs.setdefault(obj_name, {})[p.parent.name] = pd.read_csv(p, sep='\t', skiprows=1,
                                                                         header=None).to_numpy()
        # Return the outputs
        return outputs

    @classmethod
    def from_output_dir(cls, output_path: Path | str, mag_name: str):

        """
        Creates a SimtraOutput object from the directory SIMTRA wrote its results to.

        :param output_path: path to the Simtra output directory
        :param mag_name: name of the magnetron which launched the particles. SIMTRA does not store it in the output,
            so it has to be provided to file the results of the magnetron under its name
        :return: SimtraOutput object
        """

        # Convert the path from string if necessary
        output_path = Path(output_path) if isinstance(output_path, str) else output_path
        # Load the metadata from the path
        mdata = cls.load_metadata(output_path)
        # Load all averaged simulation results
        n_parts = cls.load_average_files(output_path, 'N.txt', mag_name)
        e_inc = cls.load_average_files(output_path, 'E.txt', mag_name)
        l_path = cls.load_average_files(output_path, 'Path.txt', mag_name)
        t_flight = cls.load_average_files(output_path, 'Fligth.txt', mag_name)
        n_coll = cls.load_average_files(output_path, 'NColl.txt', mag_name)
        ang_inc = cls.load_average_files(output_path, 'Ksi.txt', mag_name)
        ang_scat = cls.load_average_files(output_path, 'ScatAngle.txt', mag_name)
        # Create the Simtra output
        return cls(mdata, mag_name, n_parts, e_inc, l_path, t_flight, n_coll, ang_inc, ang_scat)

    @classmethod
    def from_file(cls, file_path: Path | str):

        """
        Creates a SimtraOutput object from a Simtra input file at a given path.

        :param file_path: path to the Simtra input file used to run the simulation
        :return: SimtraOutput object
        """

        # Convert the path from string if necessary
        file_path = Path(file_path) if isinstance(file_path, str) else file_path
        # Load the output file path and the name of the magnetron from the Simtra input file
        output_path = read_output_path_from_sin(file_path)
        mag_name = read_magnetron_name_from_sin(file_path)
        # Create the Simtra output from the output directory
        return cls.from_output_dir(output_path, mag_name)

    @staticmethod
    def merge(d1: AvgData, d2: AvgData, op: Callable[[np.ndarray, np.ndarray, str, str], np.ndarray]) -> AvgData:

        """
        Merges two nested dictionaries by combining all values of surfaces which are in both dictionaries with the
        specified operator and just transfers the ones only occurring once. Neither of the dictionaries is modified.

        :param d1: dictionary 1
        :param d2: dictionary 2
        :param op: operator which combines the values, called with both values as well as the object and surface name
        :return: merged dictionary
        """

        # Copy both levels of the first dictionary, so that the inputs stay untouched
        merged: AvgData = {obj: dict(surfs) for obj, surfs in d1.items()}
        # Add all surfaces to the first dict if not already, otherwise combine both values
        for obj, surfs in d2.items():
            m_surfs = merged.setdefault(obj, {})
            for surf, value in surfs.items():
                m_surfs[surf] = op(m_surfs[surf], value, obj, surf) if surf in m_surfs else value
        # Return the merged dictionary
        return merged

    @staticmethod
    def weights(output, obj: str, surf: str) -> np.ndarray | int:

        """
        Returns the weights of an output's averaged quantities on a surface when it is combined with another output.
        Since SIMTRA averages over the particles arriving in each cell, the weight is the number of particles per cell.
        If the number of particles was not saved for the surface, all simulations are weighted equally instead, i.e.
        by the number of simulations the output already combines.

        :param output: SimtraOutput object
        :param obj: name of the object
        :param surf: name of the surface
        :return: weights, either per cell or a single number for the whole surface
        """

        # Use the number of particles in each cell if available
        if surf in output.n_particles.get(obj, {}):
            return output.n_particles[obj][surf]
        # Otherwise, fall back to the number of combined simulations
        return len(output.metadata) if isinstance(output.metadata, list) else 1

    def weighted_average(self, output1, output2) -> Callable[[np.ndarray, np.ndarray, str, str], np.ndarray]:

        """
        Creates an operator for "merge" which averages a quantity of two outputs, weighted by the number of particles
        each of them counted per cell. Unlike the plain mean, this is exact even when more than two outputs are
        combined one after another, e.g. by "sum()", and handles cells which only one of the outputs hit.

        :param output1: SimtraOutput object 1
        :param output2: SimtraOutput object 2
        :return: operator for "merge"
        """

        def average(v1: np.ndarray, v2: np.ndarray, obj: str, surf: str) -> np.ndarray:
            # Get the weights of both outputs and broadcast them to the shape of the grid
            w1 = np.broadcast_to(self.weights(output1, obj, surf), v1.shape)
            w2 = np.broadcast_to(self.weights(output2, obj, surf), v2.shape)
            # Cells without any particles do not contribute, which also keeps a NaN of an empty cell out of the sum
            c1 = np.where(w1 > 0, w1 * v1, 0)
            c2 = np.where(w2 > 0, w2 * v2, 0)
            w = w1 + w2
            # Cells hit in neither output keep the value SIMTRA wrote for an empty cell
            with np.errstate(invalid='ignore', divide='ignore'):
                return np.where(w > 0, (c1 + c2) / np.where(w > 0, w, 1), v1)

        # Return the operator
        return average

    def merge_outputs(self, output1, output2) -> object:

        """
        Merges two SimtraOutput objects. The metadata is appended, the rest of the data is either combined by addition
        or by averaging weighted by the particle numbers.

        :param output1: SimtraOutput object 1
        :param output2: SimtraOutput object 2
        :return: merged SimtraOutput object
        """

        # Add both metadata dictionaries together. If one of them is a list already, the object already holds at
        # least two simulation results
        mdata1 = [output1.metadata] if isinstance(output1.metadata, dict) else output1.metadata
        mdata2 = [output2.metadata] if isinstance(output2.metadata, dict) else output2.metadata
        mdata = mdata1 + mdata2
        # Keep the name of the source if both outputs were launched from the same magnetron
        source = output1.source if output1.source == output2.source else None
        # Add the particle numbers together, all other quantities are averaged weighted by the particle numbers
        n_parts = self.merge(output1.n_particles, output2.n_particles, op=lambda v1, v2, obj, surf: v1 + v2)
        avg = self.weighted_average(output1, output2)
        e_inc = self.merge(output1.e_incidence, output2.e_incidence, op=avg)
        l_path = self.merge(output1.l_path, output2.l_path, op=avg)
        t_flight = self.merge(output1.t_flight, output2.t_flight, op=avg)
        n_coll = self.merge(output1.n_collisions, output2.n_collisions, op=avg)
        ang_inc = self.merge(output1.ang_incidence, output2.ang_incidence, op=avg)
        ang_scat = self.merge(output1.ang_scatter, output2.ang_scatter, op=avg)
        # Create a new class with the combined data
        return SimtraOutput(mdata, source, n_parts, e_inc, l_path, t_flight, n_coll, ang_inc, ang_scat)

    def __add__(self, other):

        """
        Manages the addition of two SimtraOutput objects. The metadata is appended, the rest of the data is either
        combined by addition or by averaging weighted by the particle numbers.

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
        either combined by addition or by averaging weighted by the particle numbers. Overriding this function is needed for making the
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
