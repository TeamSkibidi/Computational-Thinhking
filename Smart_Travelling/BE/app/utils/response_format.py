def success(message: str, data=None):
    return {
        "status": "message",
        "message": message,
        "error_message": None,
        "data": data
    }

def error(message: str):
    return {
        "status": "error_message",
        "message": None,
        "error_message": message,
        "data": None
    }