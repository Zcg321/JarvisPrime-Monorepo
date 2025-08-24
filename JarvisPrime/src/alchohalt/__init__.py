from importlib import import_module as _im
_pkg = _im("JarvisPrime.apps.alchohalt")
globals().update({k: getattr(_pkg, k) for k in dir(_pkg) if not k.startswith("_")})
