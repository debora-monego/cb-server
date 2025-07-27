# app/molecular/molecule.py
from typing import Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import logging
from .base import BaseMolecularProcessor
import os
import numpy as np
from .base import BaseMolecularProcessor, ValidationError, ComputationError
from .types import ChainSequences, CrosslinkConfig  # We'll create this file next

logger = logging.getLogger(__name__)

@dataclass
class ChainSequences:
    """Data class for triple helix chain sequences."""
    chain_a: str
    chain_b: str
    chain_c: str

@dataclass
class CrosslinkConfig:
    """Data class for crosslink configuration."""
    n_terminal_type: Optional[str] = None
    c_terminal_type: Optional[str] = None
    n_terminal_position: Optional[str] = None
    c_terminal_position: Optional[str] = None

class MoleculeGenerator(BaseMolecularProcessor):
    """Generates collagen molecule structures from sequences or templates."""
    
    VALID_AMINO_ACIDS = set('ACDEFGHIKLMNOPQRSTVWY')
    MIN_SEQUENCE_LENGTH = 1000
    MAX_SEQUENCE_LENGTH = 1100
    
    def __init__(self, output_dir: str, crosslinking_data=None):
        """
        Initialize the molecule generator.
        
        Args:
            output_dir: Directory for output files
            crosslinking_data: Instance of CrosslinkingData class
        """
        super().__init__()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.crosslinking_data = crosslinking_data
        
    def validate_sequence(self, sequence: str, chain_id: str) -> None:
        """
        Validate a single chain sequence.
        
        Args:
            sequence: Amino acid sequence
            chain_id: Chain identifier (A, B, or C)
            
        Raises:
            ValidationError: If sequence is invalid
        """
        # Clean sequence
        sequence = ''.join(sequence.split())
        
        # Length check
        if not self.MIN_SEQUENCE_LENGTH <= len(sequence) <= self.MAX_SEQUENCE_LENGTH:
            raise ValidationError(
                f"Chain {chain_id} must be between {self.MIN_SEQUENCE_LENGTH} "
                f"and {self.MAX_SEQUENCE_LENGTH} residues (current: {len(sequence)})"
            )
        
        # Amino acid validation
        invalid_chars = set(sequence) - self.VALID_AMINO_ACIDS
        if invalid_chars:
            raise ValidationError(
                f"Chain {chain_id} contains invalid amino acids: {', '.join(sorted(invalid_chars))}"
            )

    def validate_crosslinks(self, crosslinks: CrosslinkConfig, species: str) -> None:
        """
        Validate crosslink configuration against available positions.
        
        Args:
            crosslinks: CrosslinkConfig object
            species: Selected species for validation
            
        Raises:
            ValidationError: If crosslink configuration is invalid
        """
        if not self.crosslinking_data:
            return
            
        if crosslinks.n_terminal_type:
            n_positions = self.crosslinking_data.get_positions_for_type(
                species=species,
                crosslink_type=crosslinks.n_terminal_type,
                terminus='N'
            )
            if crosslinks.n_terminal_position not in n_positions:
                raise ValidationError(
                    f"Invalid N-terminal position: {crosslinks.n_terminal_position}. "
                    f"Available positions: {', '.join(sorted(n_positions))}"
                )
                
        if crosslinks.c_terminal_type:
            c_positions = self.crosslinking_data.get_positions_for_type(
                species=species,
                crosslink_type=crosslinks.c_terminal_type,
                terminus='C'
            )
            if crosslinks.c_terminal_position not in c_positions:
                raise ValidationError(
                    f"Invalid C-terminal position: {crosslinks.c_terminal_position}. "
                    f"Available positions: {', '.join(sorted(c_positions))}"
                )

    def process(self,
               chains: Optional[ChainSequences] = None,
               species: Optional[str] = None,
               crosslinks: Optional[CrosslinkConfig] = None) -> Dict[str, Any]:
        """
        Process molecule generation request.
        
        Args:
            chains: Custom chain sequences if not using template
            species: Species template name if not using custom sequences
            crosslinks: Optional crosslink configuration
            
        Returns:
            Dict containing:
                - yaml_config: Configuration for job submission
                - pdb_path: Expected path for output PDB
        """
        try:
            # Handle custom sequences
            if chains:
                # Validate each chain
                self.validate_sequence(chains.chain_a, 'A')
                self.validate_sequence(chains.chain_b, 'B')
                self.validate_sequence(chains.chain_c, 'C')
                
                sequences = {
                    'A': chains.chain_a,
                    'B': chains.chain_b,
                    'C': chains.chain_c
                }
            elif not species:
                raise ValidationError("Either custom sequences or species template must be provided")
            
            # Validate crosslinks if provided for non-custom sequences
            if crosslinks and species != 'custom':
                self.validate_crosslinks(crosslinks, species)
            
            # Prepare YAML configuration
            yaml_config = {
                'sequence_generator': True,
                'species': species if species != 'custom' else None,
                'chains': sequences if chains else None,
            }
            
            # Add crosslink configuration if provided
            if crosslinks:
                yaml_config.update({
                    'crosslink': True,
                    'n_term_type': crosslinks.n_terminal_type,
                    'c_term_type': crosslinks.c_terminal_type,
                    'n_term_combination': crosslinks.n_terminal_position,
                    'c_term_combination': crosslinks.c_terminal_position
                })
            
            # Set output paths
            pdb_path = self.output_dir / 'molecule.pdb'
            yaml_config['output'] = {
                'pdb': str(pdb_path)
            }
            
            return {
                'yaml_config': yaml_config,
                'pdb_path': str(pdb_path)
            }
            
        except Exception as e:
            logger.error(f"Error in molecule generation: {str(e)}")
            raise ComputationError(f"Failed to generate molecule: {str(e)}")

    def write_sequences_file(self, chains: ChainSequences, output_path: Path) -> None:
        """
        Write chain sequences to a file in FASTA format.
        
        Args:
            chains: ChainSequences object containing all three chains
            output_path: Path to write the sequences file
        """
        with open(output_path, 'w') as f:
            f.write(f">Chain:chainA\n{chains.chain_a}\n")
            f.write(f">Chain:chainB\n{chains.chain_b}\n")
            f.write(f">Chain:chainC\n{chains.chain_c}\n")
            
    def get_species_templates(self) -> list:
        """
        Get list of available species templates.
        
        Returns:
            List of available species names
        """
        if self.crosslinking_data:
            return [s for s in self.crosslinking_data.get_species() if s != 'custom']
        return []

    def get_crosslink_types(self) -> list:
        """
        Get list of available crosslink types.
        
        Returns:
            List of available crosslink type names
        """
        if self.crosslinking_data:
            return self.crosslinking_data.get_crosslink_types()
        return []