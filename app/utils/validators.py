# app/utils/validators.py

def validate_fasta_sequence(sequence):
    """
    Validates a FASTA sequence
    """
    if not sequence:
        return False
        
    valid_chars = set('ABCDEFGHIKLMNOPQRSTUVWXYZ-')
    sequence = sequence.upper()
    return all(char in valid_chars for char in sequence)