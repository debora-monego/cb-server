# app/molecular/config.py
"""Configuration constants for molecular computations."""

# Default parameters
DEFAULT_PARAMS = {
    'molecule': {
        'helix_pitch': 2.86,  # nm
        'rise_per_residue': 0.286,  # nm
        'atoms_per_residue': 19,
    },
    'fibril': {
        'min_contact_distance': 0.1,  # nm
        'max_contact_distance': 10.0,  # nm
        'min_length': 1.0,  # nm
        'max_length': 1000.0,  # nm
    },
    'crosslinks': {
        'max_density': 100.0,  # percentage
        'min_spacing': 0.5,  # nm
    }
}

# Force field parameters
FORCE_FIELDS = {
    'charmm36': {
        'path': 'forcefield/charmm36.ff',
        'water_model': 'tip3p',
    },
    'amber99sb-ildn': {
        'path': 'forcefield/amber99sb-ildn.ff',
        'water_model': 'tip3p',
    },
    'gromos54a7': {
        'path': 'forcefield/gromos54a7.ff',
        'water_model': 'spc',
    }
}