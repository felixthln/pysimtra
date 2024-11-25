from pathlib import Path
from datetime import datetime

from .components import Chamber, Magnetron, DummyObject
from .simtra_write import write_sin
from .simtra_read import read_sin
from .simtra import SimtraSimulation, SimtraOutput


class SputterSystem:

    """
    Class for describing a sputter system with n cathodes.
    """

    _simtra_sim: SimtraSimulation = None
    _temp_dir_path: Path = Path(__file__).parents[0] / 'temporary'

    chamber: Chamber = None
    magnetrons: list[Magnetron] = None
    dummy_objects: list[DummyObject] = None
    output_path: Path = None

    def __init__(self, chamber: Chamber, magnetrons: Magnetron | list[Magnetron],
                 dummy_objects: DummyObject | list[DummyObject], output_path: str | Path):

        """
        :param chamber: chamber object
        :param magnetrons: either a single magnetron object or a list of magnetrons
        :param dummy_objects: dummy object or list of dummy objects
        :param output_path: path pointing to a directory at which the simulation results will be stored
        """

        # If a single magnetron was provided, wrap it in a dictionary with its name as a key
        self.magnetrons = [magnetrons] if isinstance(magnetrons, Magnetron) else magnetrons
        # Assign the rest of the components to the class
        self.chamber = chamber
        self.dummy_objects = [dummy_objects] if isinstance(dummy_objects, DummyObject) else dummy_objects
        # Convert the string to a path if necessary
        self.output_path = Path(output_path) if isinstance(output_path, str) else output_path
        # Define the simulation object, by default, the path to the internal Simtra executable will be used
        self._simtra_sim = SimtraSimulation()

    @classmethod
    def single_from_file(cls, path: str | Path):

        """
        Creates a sputter system with a single magnetron from a single ".sin" file.

        :param path: path to the ".sin" file
        :return:
        """

        # Load the file and create a chamber, a magnetron and the dummy objects
        output_path, chamber, magnetron, objects = read_sin(path)
        # Create the class
        return cls(chamber, magnetron, objects, output_path)

    @classmethod
    def multiple_from_files(cls, chamber_path: str | Path, magnetron_paths: list[str | Path],
                            object_paths: list[str | Path], output_path: str | Path):

        """
        Creates a sputter system with multiple magnetrons from separate ".sin", ".smo" and/or ".sdo" files.

        :param chamber_path: Path to a ".sin" file from which the chamber object will be generated
        :param magnetron_paths: Paths to the ".smo" or ".sin" files which define the magnetrons
        :param object_paths: Paths to the ".sdo" files which define the dummy objects
        :param output_path: output path for the simulation results
        """

        # Load the chamber
        ch = Chamber.from_file(chamber_path)
        # Load the magnetron paths
        mags: list[Magnetron] = []
        for path in magnetron_paths:
            # Convert the path to a pathlib object if necessary
            path = Path(path) if isinstance(path, str) else path
            # Load the magnetron from a ".smo" or ".sin" file
            mags.append(Magnetron.from_file(path))
        # Load the dummy objects
        obj: list[DummyObject] = []
        for path in object_paths:
            # Convert the path to a pathlib object if necessary
            path = Path(path) if isinstance(path, str) else path
            # Load the dummy object file
            obj.append(DummyObject.from_file(path))
        # Create the class
        return cls(chamber=ch, magnetrons=mags, dummy_objects=obj, output_path=output_path)

    def simulate(self, magnetrons: list[str] | None = None, n_sim: int = 1) -> SimtraOutput | list[SimtraOutput]:

        """
        Performs a simulation of the sputter system by storing the components temporarily as ".sin" files
        and calling the command line version of SIMTRA. Afterward, the results directory is analyzed and the particle
        distributions of all those objects are returned which have the "save averaged data" attribute.

        :param magnetrons: list of magnetron names to simulate. If not given, the deposition from all magnetrons are
            simulated
        :param n_sim: number of simulations of each magnetron. If n > 1, seed numbers are randomly generated and all
            simulation results will be combined for each magnetron
        :return: either a single SimtraOutput object or a list of SimtraOutput objects for every simulated magnetron
            containing the simulation results
        """

        # Get a list of all magnetron names in case no list is provided
        magnetrons = [m.name for m in self.magnetrons] if not magnetrons else magnetrons
        # Get all magnetrons based on the list of names
        mags = [m for name in magnetrons for m in self.magnetrons if m.name == name]
        # mags = self.magnetrons if not magnetrons else [m for m in self.magnetrons if m.name in magnetrons]
        # Iterate over all magnetrons to store them as .sin files
        temp_sin_paths: list[Path] = []
        for mag in mags:
            # Create as many simulation files per magnetron as defined
            for i in range(n_sim):
                # Create the file path for saving the temporary file
                name = str(mag.name) + '_sim_' + str(i + 1) + '_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                sin_path = self._temp_dir_path / (name + '.sin')
                temp_sin_paths.append(sin_path)
                # Set the chambers seed number if more than one simulation needs to be done
                if n_sim > 1:
                    self.chamber.set_seed_number()
                # Get the objects of the other magnetrons and add them to the dummy object
                d_obj = self.dummy_objects + [m.m_object for m in self.magnetrons if m.name != mag.name]
                # Define the output path
                out_path = self.output_path / name
                # Save the magnetron together with the chamber and dummy objects as a SIMTRA file
                write_sin(out_path, self.chamber, mag, d_obj, sin_path)
        # Run the simulation
        sim_res = self._simtra_sim.run(temp_sin_paths, delete_input_files=True)
        # Go through the simulation results and combine results when multiple simulations of every magnetron were done
        # PyCharm does not recognize that the "sum()" function works on the SimtraOutput objects too, therefore supress
        # the warnings
        # noinspection PyTypeChecker
        results: list[SimtraOutput] = []
        for i, mag in enumerate(mags):
            # noinspection PyTypeChecker
            results.append(sum(sim_res[(i * n_sim):((i + 1) * n_sim)]))
        # Either return a list or just one output file depending on whether there is only one magnetron in the
        # sputter system
        return results if len(self.magnetrons) > 1 else results[0]

    def to_sin(self, path: str | Path, mag_name: str = None):

        """
        Saves the sputter system with a given magnetron as a single ".sin" file. In case multiple magnetrons were
        defined inside the class, the other ones are added to the file as dummy objects.

        :param path: path including a filename and the ".sin" suffix
        :param mag_name: name of the magnetron to save, for a single magnetron system, this parameter has no effect
        """

        # Convert the string to a path if necessary
        path = Path(path) if isinstance(path, str) else path
        # Get the name of the magnetron if the system only has one
        mag_name = self.magnetrons[0].name if len(self.magnetrons) == 1 else mag_name
        # If the magnetron name is not defined although multiple magnetrons were defined, raise an error
        if not mag_name:
            raise ValueError('Since multiple magnetrons are defined, specify which ones should be saved in the ".sin" '
                             'file using the "mag_name" property.')
        # Get the magnetron object from the name
        mags = [m for m in self.magnetrons if m.name == mag_name]
        # If the magnetron was not found, raise an error
        if not mags:
            raise ValueError('The magnetron with the name %s was not found.' % mag_name)
        # If one or multiple magnetrons were found, use the first one
        mag = mags[0]
        # Get the objects of the other magnetrons and add them to the dummy object
        d_obj = self.dummy_objects + [m.m_object for m in self.magnetrons if m.name != mag.name]
        # Save the magnetron together with the chamber and dummy objects as a SIMTRA file
        write_sin(path.parent, self.chamber, mag, d_obj, path)
