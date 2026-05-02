from importlib import import_module


__version__ = "0.2.3"
__all__ = ["__version__", "TwelveData"]


def __getattr__(name):
    if name not in __all__:
        raise AttributeError(f"module 'sainpse' has no attribute {name!r}")

    if name == "TwelveData":
        return import_module("sainpse.finance.data").TwelveData

    raise AttributeError(f"module 'sainpse' has no attribute {name!r}")
