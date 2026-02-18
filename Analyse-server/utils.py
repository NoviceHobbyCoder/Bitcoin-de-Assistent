def validate_api_key(api_key):
    if not api_key or len(api_key) < 32:  # Assuming a minimum length for a valid API key
        return False
    return True

def format_data(data):
    formatted_data = {}
    for key, value in data.items():
        formatted_data[key] = value if isinstance(value, (int, float, str)) else str(value)
    return formatted_data

def log_error(message):
    import logging
    logging.error(message)