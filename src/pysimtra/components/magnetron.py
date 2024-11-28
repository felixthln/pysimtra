from pathlib import Path
import pandas as pd

from .dummy_object import DummyObject


class Magnetron:

    """
    Class for describing a SIMTRA magnetron.
    """

    # Geometrical representation of the magnetron object
    m_object: DummyObject = None
    # Target parameters
    transported_element: str | None = None
    n_particles: int = None
    save_every_n_particles: int = None
    sputter_surface_index: int = None  # begins at 1
    racetrack_file_path: Path = None
    racetrack_type: str = None
    racetrack_t0: int = None
    racetrack_row_res: int = None  # in m
    racetrack_col_res: int = None  # in m
    # Transport parameters
    # Angular distribution
    angular_distribution: str = None
    cosine_coefficients: tuple[float, ...] = None
    srim_type: str = None
    srim_file_path: str = None
    # Transport description
    with_gas_motion: bool = None
    go_to_diffusion: bool = None
    interaction_potential: str = None
    screening_function: str = None
    scattering_table_path: str = None
    # Energy distribution
    energy_distribution: str = None
    surface_binding_energy: float = None
    max_ion_energy: float = None
    # Source type
    source_type: str = None

    def __init__(self,
                 transported_element: str | None,
                 m_object: DummyObject,
                 racetrack_file_path: str | Path | None,
                 n_particles: int = 10 ** 5,
                 save_every_n_particles: int = 0,
                 sputter_surface_index: int = 1,
                 racetrack_type: str = 'axialsymmetric',
                 racetrack_t0: int = 0,
                 racetrack_row_res: int = None,
                 racetrack_col_res: int = None,
                 angular_distribution: str = 'User',
                 cosine_coefficients: tuple[float, ...] = (0, 1, 0, 0, 0, 0),
                 energy_distribution: str = 'Thompson',
                 max_ion_energy: float = None,
                 surface_binding_energy: float = None,
                 with_gas_motion: bool = True,
                 go_to_diffusion: bool = True,
                 interaction_potential: str = 'screenedCoulomb',
                 screening_function: str = 'Moliere',
                 scattering_table_path: str = None,
                 srim_file_path: str = None,
                 srim_type: str = None,
                 source_type: str = 'planarTarget'):

        """
        :param transported_element: element to be sputtered
        :param m_object: DummyObject representing the geometry of the magnetron
        :param racetrack_file_path: path to the racetrack file; is used to estimate the position distribution
        :param n_particles: number of particles to simulate, defaults to 10 ** 5
        :param save_every_n_particles: defaults to zero which means the data is only saved after the simulation is done
        :param sputter_surface_index: index of the surface from which to simulate the launch of the sputtered particles,
            begins at 1
        :param racetrack_type: type of the racetrack, either "axialsymmetric", "profilometry" or "rotatable"
        :param racetrack_t0:
        :param racetrack_row_res: row resolution for the racetrack in case "profilometry" is selected as racetrack type
        :param racetrack_col_res: column resolution for the racetrack in case "profilometry" is selected
        :param angular_distribution: either "User" or "SRIM"
        :param cosine_coefficients: cosine coefficients used when the angular distribution is "User"
        :param energy_distribution: either "Thompson" or "SRIM"
        :param max_ion_energy: maximum ion energy of the sputtered element, only needed when energy distribution is
            "Thompson"
        :param surface_binding_energy: surface binding energy of the sputtered element
        :param with_gas_motion: whether the transport should be modelled with gas motion
        :param go_to_diffusion: whether the transport should be modelled with diffusion
        :param interaction_potential: either "screenedCoulomb" or "specified"
        :param screening_function: screening function when "screenedCoulomb" is selected as the interaction potential.
            Either "Moliere", "Kr-C", "Lenz-Jensen" or "ZBL"
        :param scattering_table_path: path to the scattering table
        :param srim_file_path: path to the SRIM file, only used when SRIM is used as angular or energy distribution
        :param srim_type: type of SRIM file, either "sputtered" or "backscattered", only used when SRIM is used as
            angular or energy distribution
        :param source_type: "planarTarget" most often
        """

        # Load the surface binding energies
        e_binding = pd.read_csv(Path(__file__).parents[1] / 'e_binding.csv', index_col=0).iloc[:, 0]
        # Check if the transported element is in the periodic table, allow to specify no element
        if transported_element is not None and transported_element not in e_binding.index:
            raise ValueError('Transported element %s is not a valid element.' % transported_element)
        # If no surface binding energy is specified, try to load it from the stored ones
        if transported_element is not None and surface_binding_energy is None:
            surface_binding_energy = e_binding.loc[transported_element]
            # Since the surface binding energy is needed for the simulation, raise an error if none could be found
            if surface_binding_energy is None:
                raise ValueError('For the transported element %s no surface binding energy could be found. Please '
                                 'specify one by setting "surface_binding_energy" parameter explicitly.' %
                                 transported_element)
        # Convert the racetrack path to a pathlib object
        if racetrack_file_path is not None:
            if isinstance(racetrack_file_path, str):
                racetrack_file_path = Path(racetrack_file_path)
            # In case the user works with relative file paths, resolve the path
            racetrack_file_path = racetrack_file_path.resolve()
        # Store the parameters in the class
        self.transported_element = transported_element
        self.m_object = m_object
        self.racetrack_file_path = racetrack_file_path
        self.n_particles = n_particles
        self.save_every_n_particles = save_every_n_particles
        self.sputter_surface_index = sputter_surface_index
        self.racetrack_type = racetrack_type
        self.racetrack_t0 = racetrack_t0
        self.racetrack_row_res = racetrack_row_res
        self.racetrack_col_res = racetrack_col_res
        self.angular_distribution = angular_distribution
        self.cosine_coefficients = cosine_coefficients
        self.energy_distribution = energy_distribution
        self.max_ion_energy = max_ion_energy
        self.surface_binding_energy = surface_binding_energy
        self.with_gas_motion = with_gas_motion
        self.go_to_diffusion = go_to_diffusion
        self.interaction_potential = interaction_potential
        self.screening_function = screening_function
        self.scattering_table_path = scattering_table_path
        self.srim_file_path = srim_file_path
        self.srim_type = srim_type
        self.source_type = source_type

    @classmethod
    def from_file(cls, path: str | Path):

        """
        Creates a Magnetron object from a given ".smo" file or ".sin" file. In case of a ".sin" file, only the
        "Source" section will be parsed.

        :param path: path to the simtra magnetron object file with ending ".smo" or the simtra input file ".sin"
        :return: Magnetron object
        """

        # Import the method here to avoid circular imports
        from ..simtra_read import read_sin, read_smo
        # Convert the string to a path if necessary
        path = Path(path) if isinstance(path, str) else path
        # Load the file and initialize the class
        return read_sin(path, only_magnetron=True) if path.suffix == '.sin' else read_smo(path)

    # Property function to allow the access to the magnetron name without accessing it through the dummy object
    @property
    def name(self) -> str:
        return self.m_object.name

    # Property function to allow setting to the magnetron name without accessing it through the dummy object
    @name.setter
    def name(self, value: str):
        self.m_object.name = value

    # :- Magic functions

    def __eq__(self, other) -> bool:

        # Check if the second object is a Magnetron too
        if isinstance(other, Magnetron):
            # Check if the parameters of both classes are identical
            return vars(self) == vars(other)
        # In any other case, return an error
        return NotImplemented

    # :- Conversion functions

    def to_smo(self, path: str | Path) -> None:

        """
        Stores the magnetron object as a Simtra magnetron object file (with file ending ".smo").

        :param path: path at which the simtra magnetron object ".smo" should be stored
        :return:
        """

        # Import the method here to avoid circular imports
        from ..simtra_write import write_smo
        # Convert the string to a path if necessary
        path = Path(path) if isinstance(path, str) else path
        # Save the smo file
        write_smo(self, path)
