def singleton(callable_obj):
    """A simple singleton decorator for classes/functions and other callable objects."""
    instances = {}

    def wrapper(*args, **kwargs):
        if callable_obj not in instances:
            instances[callable_obj] = callable_obj(*args, **kwargs)
        return instances[callable_obj]

    return wrapper
