from dataclasses import dataclass
from typing import Optional

@dataclass
class ChainSequences:
    chain_a: str
    chain_b: str
    chain_c: str

@dataclass
class CrosslinkConfig:
    n_terminal_type: str
    c_terminal_type: str
    n_terminal_position: Optional[int] = None
    c_terminal_position: Optional[int] = None