import sys

if sys.version_info >= (3, 12):
    import pymorphy3 as pymorphy2
    from pymorphy3.shapes import restore_capitalization
else:
    import pymorphy2
    from pymorphy2.shapes import restore_capitalization

__all__ = ["pymorphy2", "restore_capitalization"]
