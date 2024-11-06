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
    magnetrons: dict[str | int, Magnetron] = None
    dummy_objects: list[DummyObject] = None
    output_path: Path = None

    def __init__(self, chamber: Chamber, magnetrons: Magnetron | dict[str | int, Magnetron],
                 dummy_objects: DummyObject | list[DummyObject], output_path: str | Path):

        """
        Creates a combinatorial sputtering system from a chamber, magnetrons and objects. For each magnetron, a Simtra
        simulation is triggered.

        :param chamber: chamber object
        :param magnetrons: either a single magnetron object or a dictionary of magnetrons with the keys being their
        names, represented either by a string or an integer. The names don't necessarily need to be the names specified
        in the magnetron object itself. The keys can be used to specify whether the deposition from only a subset of
        magnetrons should be simulated
        :param dummy_objects: dummy object or list of dummy objects
        :param output_path: path pointing to a directory at which the simulation results will be stored
        """

        # If a single magnetron was provided, wrap it in a dictionary with its name as a key
        self.magnetrons = {magnetrons.m_object.name: magnetrons} if isinstance(magnetrons, Magnetron) else magnetrons
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
    def multiple_from_files(cls, chamber_path: str | Path, magnetron_paths: dict[str | int, str | Path],
                            object_paths: list[str | Path], output_path: str | Path):

        """
        Creates a sputter system with multiple magnetrons from separate ".sin", ".smo" and/or ".sdo" files.

        :param chamber_path: Path to a ".sin" file from which the chamber object will be generated
        :param magnetron_paths: Paths to the ".smo" or ".sin" files which define the magnetrons
        :param object_paths: Paths to the ".sdo" files which define the dummy objects
        :param output_path: output path for the simulation results
        :return:
        """

        # Load the chamber
        ch = Chamber.from_file(chamber_path)
        # Load the magnetron paths
        mags = {}
        for name, path in magnetron_paths.items():
            # Convert the path to a pathlib object if necessary
            path = Path(path) if isinstance(path, str) else path
            # Load the magnetron from a ".smo" or ".sin" file
            mags[name] = Magnetron.from_file(path)
        # Load the dummy objects
        obj = []
        for path in object_paths:
            # Convert the path to a pathlib object if necessary
            path = Path(path) if isinstance(path, str) else path
            # Load the dummy object file
            obj.append(DummyObject.from_file(path))
        # Create the class
        return cls(chamber=ch, magnetrons=mags, dummy_objects=obj, output_path=output_path)

    def set_ion_energies(self, energies: float | dict[str | int, float]):

        """
        Changes the maximum ion energy/energies of the sputtering system.

        :param energies: either a float if there is just one cathode or a dictionary containing the names of the
        magnetrons as keys and the maximum ion energies of the magnetrons as values
        :return:
        """

        # If a float is given, convert it to a dictionary
        energies = {list(self.magnetrons.keys())[0]: energies} if isinstance(energies, float) else energies
        # Change the ion energies of the magnetrons
        for mag_name, volt in energies.items():
            self.magnetrons[mag_name].max_ion_energy = volt

    def simulate(self, magnetrons: list[str | int] | None = None,
                 n_sim: int = 1) -> SimtraOutput | dict[str | int, SimtraOutput]:

        """
        Performs a simulation of the sputtering system by storing the components temporarily as ".sin" files
        and calling the command line version of Simtra. Afterward, the results directory is analyzed and the particle
        distributions of all those objects are returned which have the "save averaged data" attribute.

        :param magnetrons: list of magnetron names to simulate. If not given, the deposition of all magnetrons are
        simulated
        :param n_sim: number of simulations of each magnetron. If n > 1, seed numbers are randomly generated and all
        simulation results will be combined for each magnetron
        :return: either a single SimtraOutput object or a dictionary of SimtraOutput objects for every simulated
        magnetron containing the simulation results
        """

        # If a list of magnetrons was not given, use all keys from the magnetron dictionary
        magnetrons = list(self.magnetrons.keys()) if magnetrons is None else magnetrons
        # Save the sputter system as multiple .sin files into the temporary input directory
        temp_sin_paths: list[Path] = []
        for mag_key in magnetrons:
            # Check the magnetron exists and throw an error if not
            if mag_key not in self.magnetrons.keys():
                raise ValueError('There is no magnetron with the name "%s".' % mag_key)
            # Create as many simulation files as indicated with the magnetrons dictionary
            for i in range(n_sim):
                # Create the file path for saving the temporary file
                name = 'mag_' + str(mag_key) + '_sim_' + str(i+1) + '_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                sin_path = self._temp_dir_path / (name + '.sin')
                temp_sin_paths.append(sin_path)
                # Set the chambers seed number if more than one simulation needs to be done
                if n_sim > 1:
                    self.chamber.set_seed_number()
                # Get the magnetron from the given magnetron key
                mag = self.magnetrons[mag_key]
                # Get the objects of the other magnetrons and add them to the dummy object
                d_obj = self.dummy_objects + [m.m_object for n, m in self.magnetrons.items() if n != mag_key]
                # Define the output path
                out_path = self.output_path / name
                # Save the magnetron together with the chamber and dummy objects as a Simtra file
                write_sin(out_path, self.chamber, mag, d_obj, sin_path)
        # Run the simulation
        sim_res = self._simtra_sim.run(temp_sin_paths, delete_input_files=True)
        # Go through the simulation results and combine results when multiple simulations of every magnetron were done
        # PyCharm does not recognize that the "sum()" function works on the SimtraOutput objects too, therefore supress
        # the warnings
        # noinspection PyTypeChecker
        results: dict[str | int, SimtraOutput] = {}
        for i, mag_key in enumerate(magnetrons):
            # noinspection PyTypeChecker
            results[mag_key] = sum(sim_res[(i * n_sim):((i+1) * n_sim)])
        # Either return a dictionary or just one output file depending on whether there is only one magnetron in the
        # sputter system
        return results if len(self.magnetrons) > 1 else results[list(results.keys())[0]]

    def to_sin(self, path: str | Path, mag_key: str | int = None):

        """
        Saves the sputter system with a given magnetron as a single ".sin" file. In case multiple magnetrons were
        defined inside the class, the other ones are added to the file as dummy objects.

        :param path: path including a filename and the ".sin" suffix
        :param mag_key: key of the magnetron to save, for a single magnetron system, this parameter has no effect
        :return:
        """

        # Convert the string to a path if necessary
        path = Path(path) if isinstance(path, str) else path
        # If there is only one magnetron, infer the magnetron key
        mag_key = list(self.magnetrons.keys())[0] if len(self.magnetrons) == 1 else mag_key
        # If there is no magnetron key given but there are multiple ones, raise an error
        if mag_key is None:
            raise ValueError('Since multiple magnetrons are defined, specify which ones should be saved in the ".sin" '
                             'file using the "mag_key" property.')
        # Get the magnetron from the given magnetron key
        mag = self.magnetrons[mag_key]
        # Get the objects of the other magnetrons and add them to the dummy object
        d_obj = self.dummy_objects + [m.m_object for n, m in self.magnetrons.items() if n != mag_key]
        # Save the magnetron together with the chamber and dummy objects as a Simtra file
        write_sin(path.parent, self.chamber, mag, d_obj, path)
