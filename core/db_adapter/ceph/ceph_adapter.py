import fnmatch
import ssl
import sys
import types

if sys.version_info >= (3, 12):
    # `boto` (the legacy, unmaintained v2 SDK) is incompatible out of the box with
    # Python 3.12+: it vendors a very old `six` (whose meta path importer predates
    # PEP 451 and is silently ignored by 3.12+'s import system) and unconditionally
    # imports the `imp` module, which was removed in 3.12. Neither issue is hit by
    # the functionality this adapter actually relies on (plain S3 connection/IO), so
    # we patch them up before `boto` is imported for the first time.
    if "imp" not in sys.modules:
        def _imp_removed(*_args, **_kwargs):
            raise ModuleNotFoundError(
                "The 'imp' module was removed in Python 3.12. This compatibility "
                "shim (added for the legacy 'boto' package) does not implement "
                "boto's plugin loading, which this framework does not use."
            )

        _imp_stub = types.ModuleType("imp")
        _imp_stub.find_module = _imp_removed
        _imp_stub.load_module = _imp_removed
        sys.modules["imp"] = _imp_stub

    if "boto.vendored.six" not in sys.modules:
        import importlib.util

        import six as _six

        _spec = importlib.util.spec_from_file_location("boto.vendored.six", _six.__file__)
        _boto_six = importlib.util.module_from_spec(_spec)
        sys.modules["boto.vendored.six"] = _boto_six
        _spec.loader.exec_module(_boto_six)

import boto
import boto.s3.connection as s3_connection
from boto.exception import BotoServerError, BotoClientError

import core.logging.logger_constants as log_const
from core.db_adapter.ceph.ceph_io import CephIO
from core.db_adapter.db_adapter import DBAdapter
from core.logging.logger_utils import log
from core.monitoring.monitoring import monitoring

ssl._create_default_https_context = ssl._create_unverified_context


class CephAdapter(DBAdapter):
    def __init__(self, config):
        self._bucket = None
        super().__init__(config)

    def connect(self):
        try:
            self._client = boto.connect_s3(
                aws_access_key_id=self.config["access_key"],
                aws_secret_access_key=self.config["secret_key"],
                host=self.config["host"],
                is_secure=self.config["is_secure"],
                port=self.config["port"],
                calling_format=s3_connection.OrdinaryCallingFormat(),
            )
            self._bucket = self._client.get_bucket(self.config["bucket"])
        except Exception:
            log("CephAdapter connect error",
                params={log_const.KEY_NAME: log_const.HANDLED_EXCEPTION_VALUE},
                level="ERROR",
                exc_info=True)
            monitoring.got_counter("ceph_connection_exception")
            raise

    @property
    def _handled_exception(self):
        return BotoServerError, BotoClientError

    @property
    def source(self):
        return self

    def _list_dir(self, path):
        return [key.name for key in self._bucket.list(prefix=path)]

    def _open(self, filename, mode, *args, **kwargs):
        io_config = {"filename": filename,
                     "mode": mode,
                     "bucket": self._bucket,
                     "try_count": self.config.get("read_tries")}
        return CephIO(io_config)

    def _on_prepare(self):
        self.connect()

    def _get_counter_name(self):
        return "ceph_adapter"

    def _glob(self, path, pattern):
        files_list = self._list_dir(path)
        filtered = fnmatch.filter(files_list, pattern)
        return filtered

    def _path_exists(self, path):
        return bool(self._list_dir(path))

    def _mtime(self, path):
        key = self._bucket.get_key(path)
        if key and key.last_modified:
            return key.last_modified
