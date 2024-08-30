def is_positive_float(s):
    try:
        float_value = float(s)
        return float_value >= 0
    except ValueError:
        return False
    
def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False
    
        
def is_float(s):
    try:
        float_value = float(s)
    except ValueError:
        return False
    return True
    
def is_boolean(value):
    return isinstance(value, bool)
    
def is_positive_range(min_p, max_p):
    if not (is_positive_float(min_p) and is_positive_float(max_p)):
        return False
    if float(min_p) < float(max_p):
        return True
    return False
    
def is_percentage_range(min_p, max_p):
    if not is_positive_range(min_p, max_p):
        return False
    if 0 <= float(min_p) <= 100 and 0 <= float(max_p) <= 100:
        return True
    return False
