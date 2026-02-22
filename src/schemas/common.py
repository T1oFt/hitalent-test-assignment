from enum import Enum

class TransferMode(str, Enum):
    """Режимы удаления департамента."""
    cascade = "cascade"
    reassign = "reassign"