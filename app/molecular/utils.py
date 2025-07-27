# app/molecular/utils.py
import numpy as np
from typing import List, Tuple, Dict

def calculate_center_of_mass(coordinates: np.ndarray) -> np.ndarray:
    """Calculate center of mass for a set of coordinates."""
    return np.mean(coordinates, axis=0)

def calculate_distance_matrix(coords1: np.ndarray, coords2: np.ndarray) -> np.ndarray:
    """Calculate distance matrix between two sets of coordinates."""
    return np.linalg.norm(coords1[:, np.newaxis] - coords2, axis=2)

def parse_pdb_coordinates(pdb_data: str) -> np.ndarray:
    """Extract coordinates from PDB data."""
    coordinates = []
    for line in pdb_data.splitlines():
        if line.startswith('ATOM'):
            try:
                x = float(line[30:38])
                y = float(line[38:46])
                z = float(line[46:54])
                coordinates.append([x, y, z])
            except ValueError:
                continue
    return np.array(coordinates)