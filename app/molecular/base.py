# app/molecular/base.py
from abc import ABC, abstractmethod
from typing import Optional, Protocol, Dict, Any, List, Tuple, Union
import numpy as np
from pathlib import Path
import logging
from datetime import datetime
import yaml

# Setup logging
logger = logging.getLogger(__name__)

class ProgressCallback(Protocol):
    """Protocol for progress callback functions."""
    def __call__(self, progress: float, message: str) -> None: ...

class MolecularConfig:
    """Class to handle YAML configuration."""
    def __init__(self, config_data: Dict[str, Any]):
        self.data = config_data
        
    @classmethod
    def from_yaml(cls, yaml_path: Union[str, Path]) -> 'MolecularConfig':
        """Load configuration from YAML file."""
        with open(yaml_path, 'r') as f:
            return cls(yaml.safe_load(f))
            
    def to_yaml(self, yaml_path: Union[str, Path]) -> None:
        """Save configuration to YAML file."""
        with open(yaml_path, 'w') as f:
            yaml.dump(self.data, f, default_flow_style=False)
            
    def update(self, **kwargs) -> None:
        """Update configuration with new values."""
        self.data.update(kwargs)

class MolecularResult:
    """Class to store molecular computation results."""
    def __init__(self, 
                 success: bool,
                 message: str,
                 config: MolecularConfig,
                 data: Dict[str, Any] = None,
                 files: Dict[str, Path] = None):
        self.success = success
        self.message = message
        self.config = config
        self.data = data or {}
        self.files = files or {}
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'message': self.message,
            'config': self.config.data,
            'data': self.data,
            'files': {k: str(v) for k, v in self.files.items()},
            'timestamp': self.timestamp.isoformat()
        }

class BaseMolecularProcessor(ABC):
    """Base class for all molecular processors."""
    
    def __init__(self, 
                 output_dir: Union[str, Path],
                 config: Optional[MolecularConfig] = None,
                 progress_callback: Optional[ProgressCallback] = None,
                 debug: bool = False):
        self.output_dir = Path(output_dir)
        self.config = config
        self.progress_callback = progress_callback
        self.debug = debug
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def update_progress(self, progress: float, message: str = "") -> None:
        """Update computation progress."""
        if self.progress_callback:
            progress = max(0.0, min(1.0, progress))
            self.progress_callback(progress, message)
            
        if self.debug:
            self.logger.debug(f"Progress {progress*100:.1f}%: {message}")

    def run_subprocess(self, command: List[str]) -> Tuple[bool, str]:
        """Run external command."""
        import subprocess
        try:
            result = subprocess.run(
                command,
                cwd=str(self.output_dir),
                text=True,
                capture_output=True,
                check=True
            )
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            return False, e.stderr

    @abstractmethod
    def validate_input(self) -> Tuple[bool, str]:
        """Validate configuration."""
        pass

    @abstractmethod
    def process(self) -> MolecularResult:
        """Process the molecular computation."""
        pass

class ValidationError(Exception):
    """Raised when input validation fails."""
    pass

class ComputationError(Exception):
    """Raised when molecular computation fails."""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message)
        self.details = details or {}

class SequenceValidator:
    """Utility class for validating molecular sequences."""
    
    @staticmethod
    def validate_amino_acid_sequence(sequence: str) -> Tuple[bool, str]:
        """Validate amino acid sequence."""
        valid_amino_acids = set('ACDEFGHIKLMNPQRSTVWY')
        sequence = sequence.upper().strip()
        
        if not sequence:
            return False, "Sequence is empty"
            
        invalid_chars = set(sequence) - valid_amino_acids
        if invalid_chars:
            return False, f"Invalid amino acids found: {', '.join(invalid_chars)}"
            
        return True, "Sequence is valid"

    @staticmethod
    def validate_chain_lengths(chains: List[str]) -> Tuple[bool, str]:
        """Validate that chain lengths match."""
        if not chains:
            return False, "No chains provided"
            
        lengths = [len(chain) for chain in chains]
        if len(set(lengths)) != 1:
            return False, f"Chain lengths do not match: {lengths}"
            
        return True, "Chain lengths match"

def setup_molecular_logger(debug: bool = False) -> None:
    """Setup logger for molecular computations."""
    level = logging.DEBUG if debug else logging.INFO
    
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    logger = logging.getLogger(__name__)
    logger.setLevel(level)
    logger.addHandler(handler)