# app/molecular/validators.py
from typing import Dict, Any
import numpy as np

class StructureValidator:
    """Validates molecular structures and parameters."""
    
    @staticmethod
    def validate_pdb_structure(pdb_data: str) -> bool:
        """Validate PDB file format and content."""
        try:
            lines = pdb_data.splitlines()
            
            # Basic PDB format validation
            for line in lines:
                if line.startswith('ATOM'):
                    # Validate atom record format
                    if len(line) < 54:  # Minimum length for coordinates
                        return False
                    
                    # Try parsing coordinates
                    try:
                        x = float(line[30:38])
                        y = float(line[38:46])
                        z = float(line[46:54])
                    except ValueError:
                        return False
            
            return True
        except Exception:
            return False

    @staticmethod
    def validate_crosslinks(crosslinks: Dict[str, Any]) -> bool:
        """Validate crosslink specifications."""
        required_fields = {'type', 'position', 'parameters'}
        return all(field in crosslinks for field in required_fields)

    @staticmethod
    def validate_contact_distance(distance: float) -> bool:
        """Validate contact distance between molecules."""
        return 0.1 <= distance <= 10.0