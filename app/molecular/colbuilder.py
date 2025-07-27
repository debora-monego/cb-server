# app/molecular/colbuilder.py

import os
import subprocess
import logging
import yaml
from pathlib import Path
from typing import Callable, Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)

def generate_collagen_molecule(
    sequence_data: Dict[str, Any],
    crosslinks: Optional[Dict[str, Any]] = None,
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> str:
    """
    Generate a collagen molecule structure using colbuilder.
    
    Args:
        sequence_data: Dictionary containing sequence information
        crosslinks: Optional crosslink configuration
        progress_callback: Optional callback for progress updates
    
    Returns:
        str: Path to generated PDB file
    """
    try:
        if progress_callback:
            progress_callback(0.2, "Preparing sequence data")
            
        # Create working directory
        work_dir = Path(sequence_data.get('working_directory', './'))
        work_dir.mkdir(parents=True, exist_ok=True)
        
        # Prepare YAML configuration
        config = {
            'sequence_generator': True,
            'geometry_generator': False,
            'topology_generator': False,
            'debug': False,
            'working_directory': str(work_dir)
        }
        
        # Add sequence data
        if sequence_data.get('species'):
            config['species'] = sequence_data['species']
        elif sequence_data.get('chains'):
            config['chains'] = sequence_data['chains']
        else:
            raise ValueError("Either species or chain sequences must be provided")
            
        if progress_callback:
            progress_callback(0.3, "Adding crosslink configuration")
            
        # Add crosslink configuration
        if crosslinks:
            config.update({
                'crosslink': True,
                'n_term_type': crosslinks.get('n_terminal_type'),
                'c_term_type': crosslinks.get('c_terminal_type'),
                'n_term_combination': crosslinks.get('n_terminal_position'),
                'c_term_combination': crosslinks.get('c_terminal_position')
            })
            
        if progress_callback:
            progress_callback(0.4, "Writing configuration")
            
        # Write configuration file
        config_path = work_dir / 'molecule_config.yaml'
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
            
        if progress_callback:
            progress_callback(0.5, "Running colbuilder")
            
        # Run colbuilder
        result = subprocess.run(
            ['/opt/venv/bin/colbuilder', '--config_file', str(config_path)],
            capture_output=True,
            text=True,
            check=True
        )
        
        if progress_callback:
            progress_callback(0.9, "Processing output")
            
        # Check for expected output file
        output_pdb = work_dir / 'molecule.pdb'
        if not output_pdb.exists():
            raise FileNotFoundError("Expected PDB file not generated")
            
        if progress_callback:
            progress_callback(1.0, "Molecule generation complete")
            
        return str(output_pdb)
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Colbuilder execution failed: {e.stderr}")
        raise RuntimeError(f"Colbuilder execution failed: {e.stderr}")
    except Exception as e:
        logger.error(f"Error in molecule generation: {str(e)}")
        raise

def create_collagen_fibril(
    input_molecule: str,
    contact_distance: float,
    length: float,
    generate_gromacs: bool = False,
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> Tuple[str, Optional[Dict[str, str]]]:
    """
    Create a collagen fibril structure.
    
    Args:
        input_molecule: Path to input molecule PDB
        contact_distance: Contact distance in Angstroms
        length: Fibril length in nm
        generate_gromacs: Whether to generate GROMACS files
        progress_callback: Optional callback for progress updates
    
    Returns:
        Tuple[str, Optional[Dict[str, str]]]: Path to PDB file and optional GROMACS files
    """
    try:
        if progress_callback:
            progress_callback(0.2, "Preparing fibril configuration")
            
        # Create working directory
        work_dir = Path(os.path.dirname(input_molecule))
        
        # Prepare YAML configuration
        config = {
            'sequence_generator': False,
            'geometry_generator': True,
            'topology_generator': generate_gromacs,
            'debug': False,
            'working_directory': str(work_dir),
            'pdb_file': input_molecule,
            'contact_distance': contact_distance,
            'fibril_length': length
        }
        
        if progress_callback:
            progress_callback(0.3, "Writing configuration")
            
        # Write configuration file
        config_path = work_dir / 'fibril_config.yaml'
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
            
        if progress_callback:
            progress_callback(0.4, "Running colbuilder")
            
        # Run colbuilder
        result = subprocess.run(
            ['/opt/venv/bin/colbuilder', '--config_file', str(config_path)],
            capture_output=True,
            text=True,
            check=True
        )
        
        if progress_callback:
            progress_callback(0.8, "Processing output")
            
        # Collect output files
        output_pdb = work_dir / 'fibril.pdb'
        if not output_pdb.exists():
            raise FileNotFoundError("Expected PDB file not generated")
            
        gromacs_files = None
        if generate_gromacs:
            gromacs_files = {}
            for ext in ['.top', '.gro', '.mdp']:
                path = work_dir / f'fibril{ext}'
                if path.exists():
                    gromacs_files[ext[1:]] = str(path)
                    
        if progress_callback:
            progress_callback(1.0, "Fibril generation complete")
            
        return str(output_pdb), gromacs_files
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Colbuilder execution failed: {e.stderr}")
        raise RuntimeError(f"Colbuilder execution failed: {e.stderr}")
    except Exception as e:
        logger.error(f"Error in fibril generation: {str(e)}")
        raise

def modify_crosslinks(
    input_structure: str,
    modification_type: str,
    parameters: Dict[str, Any],
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> str:
    """
    Modify crosslinks in a structure.
    
    Args:
        input_structure: Path to input PDB
        modification_type: Type of modification ('mix' or 'density')
        parameters: Modification parameters
        progress_callback: Optional callback for progress updates
    
    Returns:
        str: Path to modified PDB file
    """
    try:
        if progress_callback:
            progress_callback(0.2, "Preparing modification configuration")
            
        # Create working directory
        work_dir = Path(os.path.dirname(input_structure))
        
        # Prepare YAML configuration
        config = {
            'sequence_generator': False,
            'geometry_generator': False,
            'topology_generator': False,
            'modification': {
                'type': modification_type,
                'parameters': parameters
            },
            'debug': False,
            'working_directory': str(work_dir),
            'pdb_file': input_structure
        }
        
        if progress_callback:
            progress_callback(0.3, "Writing configuration")
            
        # Write configuration file
        config_path = work_dir / 'modification_config.yaml'
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
            
        if progress_callback:
            progress_callback(0.4, "Running colbuilder")
            
        # Run colbuilder
        result = subprocess.run(
            ['/opt/venv/bin/colbuilder', '--config_file', str(config_path)],
            capture_output=True,
            text=True,
            check=True
        )
        
        if progress_callback:
            progress_callback(0.9, "Processing output")
            
        # Check for output file
        output_pdb = work_dir / 'modified.pdb'
        if not output_pdb.exists():
            raise FileNotFoundError("Expected PDB file not generated")
            
        if progress_callback:
            progress_callback(1.0, "Modification complete")
            
        return str(output_pdb)
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Colbuilder execution failed: {e.stderr}")
        raise RuntimeError(f"Colbuilder execution failed: {e.stderr}")
    except Exception as e:
        logger.error(f"Error in crosslink modification: {str(e)}")
        raise

def change_density(
    input_structure: str,
    target_density: float,
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> str:
    """
    Change crosslink density in a structure.
    
    Args:
        input_structure: Path to input PDB
        target_density: Target crosslink density percentage
        progress_callback: Optional callback for progress updates
    
    Returns:
        str: Path to modified PDB file
    """
    return modify_crosslinks(
        input_structure,
        'density',
        {'target_density': target_density},
        progress_callback
    )