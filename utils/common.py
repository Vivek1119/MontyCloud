import uuid
from datetime import datetime


def generate_uuid() -> str:
    """
        Generate a unique UUID string.
    """
    return str(uuid.uuid4())

def current_timestamp() -> str:
    """
        Return current UTC timestamp as ISO string.
    """
    return datetime.now().isoformat()