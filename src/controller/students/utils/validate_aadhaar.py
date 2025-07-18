# src/controller/utils/verhoeff.py

def is_valid_aadhaar(aadhaar_number: str) -> bool:
    """
    Validates a 12-digit Aadhaar number using the Verhoeff algorithm.

    Args:
        aadhaar_number (str): Aadhaar number as a string. Can include hyphens or spaces.

    Returns:
        bool: True if the Aadhaar number is valid, False otherwise.
    """

    # Remove non-digit characters like hyphens or spaces
    aadhaar_number = ''.join(filter(str.isdigit, aadhaar_number))

    if len(aadhaar_number) != 12:
        return False

    # Verhoeff multiplication table
    d_table = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
        [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
        [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
        [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
        [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
        [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
        [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
        [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
        [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
    ]

    # Verhoeff permutation table
    p_table = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
        [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
        [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
        [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
        [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
        [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
        [7, 0, 4, 6, 9, 1, 3, 2, 5, 8]
    ]

    checksum = 0
    for i, digit in enumerate(reversed(aadhaar_number)):
        checksum = d_table[checksum][p_table[i % 8][int(digit)]]

    return checksum == 0


def make_aadhaar_clean(aadhaar: str):
    if not aadhaar:
        return None
    aadhaar = aadhaar.replace('-', '').replace(' ', '')
    return aadhaar

def verify_aadhaar(aadhaar):
    clean_aadhaar = make_aadhaar_clean(aadhaar)
    if not clean_aadhaar:
        raise ValueError('There shoulf be 12 digits in aadhaar number')
        
    result = is_valid_aadhaar(clean_aadhaar)
    
    if result:
        return clean_aadhaar
    
    raise ValueError('Invalid Aadhaar Number')

    
