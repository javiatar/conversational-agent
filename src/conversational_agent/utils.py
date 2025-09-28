import os
from pathlib import Path


def singleton(callable_obj):
    """A simple singleton decorator for classes/functions and other callable objects."""
    instances = {}

    def wrapper(*args, **kwargs):
        if callable_obj not in instances:
            instances[callable_obj] = callable_obj(*args, **kwargs)
        return instances[callable_obj]

    return wrapper


# Handles both local development and containerized paths
if os.path.exists("/app/storage"):
    STORAGE_PATH = Path("/app/storage")  # Only present in container path
else:
    STORAGE_PATH = Path(__file__).parent.parent.parent / "storage"  # Local development path
