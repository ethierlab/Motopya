def is_positive_float(s):
    try:
        float_value = float(s)
        print(float_value >= 0)
        return float_value >= 0
    except ValueError:
        return False
    
def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False
    
def is_positive_float(s):
    try:
        float_value = float(s)
        return float_value >= 0
    except ValueError:
        return False
    
def is_boolean(value):
    return isinstance(value, bool)
    
    
