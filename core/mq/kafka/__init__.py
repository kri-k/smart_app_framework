import sys
import types

if sys.version_info >= (3, 12):
    # `kafka-python` (pinned to an old release for compatibility with `aiokafka`)
    # vendors a very old `six` whose meta path importer predates PEP 451 and is
    # silently ignored by Python 3.12+'s import system, breaking imports such as
    # `kafka.consumer.fetcher` (used transitively by `aiokafka`). We swap it out
    # for the real (actively maintained, PEP 451-compatible) `six` package before
    # `kafka`/`aiokafka` are imported for the first time.
    if "kafka.vendor.six" not in sys.modules:
        import importlib.util

        import six as _six

        _spec = importlib.util.spec_from_file_location("kafka.vendor.six", _six.__file__)
        _kafka_six = importlib.util.module_from_spec(_spec)
        sys.modules["kafka.vendor.six"] = _kafka_six
        _spec.loader.exec_module(_kafka_six)
