DefaultKWArgs = {}


def try_get_kwarg(customargs, kwarg, default=None):
    """
    Try to get a kwarg from customargs, and if it's not there, get it from
    DefaultKWArgs.
    """
    if kwarg in customargs:
        return customargs.pop(kwarg)
    else:
        return DefaultKWArgs.get(kwarg, default)