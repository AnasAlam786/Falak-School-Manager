# src/controller/add_student/utills/validate_name.py

def validate_length( value: any, name: str, *, exact: int | None = None, 
                     min_len: int | None = None, max_len: int | None = None, 
                     allow_empty: bool = False ) -> None:    
    s = (value or "").strip()


    if allow_empty and not s:
        return None
    if not s:
        raise Exception(f"{name} is required.")

    L = len(s)

    if exact is not None and L != exact:
        raise Exception(f"{name} must be exactly {exact} characters (got {L}).")
    if min_len is not None and L < min_len:
        raise Exception(f"{name} must be at least {min_len} characters (got {L}).")
    if max_len is not None and L > max_len:
        raise Exception(f"{name} must be at most {max_len} characters (got {L}).")
