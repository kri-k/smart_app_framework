import fnmatch
import ssl
import sys

import core.logging.logger_constants as log_const
from core.db_adapter.ceph.ceph_io import CephIO
from core.db_adapter.db_adapter import DBAdapter
from core.logging.logger_utils import log
from core.monitoring.monitoring import monitoring

ssl._create_default_https_context = ssl._create_unverified_context

if sys.version_info < (3, 12):
    import boto
    import boto.s3.connection as s3_connection
    from boto.exception import BotoServerError, BotoClientError

    _CEPH_EXCEPTIONS = (BotoServerError, BotoClientError)
else:
    import boto3
    from botocore.config import Config
    from botocore.exceptions import BotoCoreError, ClientError

    _CEPH_EXCEPTIONS = (ClientError, BotoCoreError)

    class _Boto3Key:
        def __init__(self, client, bucket_name, key_name, last_modified=None):
            self.client = client
            self.bucket_name = bucket_name
            self.name = key_name
            self.last_modified = last_modified

        def get_contents_as_string(self):
            response = self.client.get_object(Bucket=self.bucket_name, Key=self.name)
            return response["Body"].read()

    class _Boto3Bucket:
        def __init__(self, client, bucket_name):
            self.client = client
            self.name = bucket_name

        def list(self, prefix=""):
            paginator = self.client.get_paginator("list_objects_v2")
            keys = []
            for page in paginator.paginate(Bucket=self.name, Prefix=prefix):
                for obj in page.get("Contents", []):
                    keys.append(_Boto3Key(self.client, self.name, obj["Key"], obj.get("LastModified")))
            return keys

        def get_key(self, key_name):
            try:
                response = self.client.head_object(Bucket=self.name, Key=key_name)
            except ClientError as error:
                if error.response.get("Error", {}).get("Code") in {"404", "NoSuchKey", "NotFound"}:
                    return None
                raise
            return _Boto3Key(
                self.client,
                self.name,
                key_name,
                response.get("LastModified"),
            )


class CephAdapter(DBAdapter):
    def __init__(self, config):
        self._bucket = None
        self._client = None
        super(CephAdapter, self).__init__(config)

    def connect(self):
        try:
            if sys.version_info < (3, 12):
                self._client = boto.connect_s3(
                    aws_access_key_id=self.config["access_key"],
                    aws_secret_access_key=self.config["secret_key"],
                    host=self.config["host"],
                    is_secure=self.config["is_secure"],
                    port=self.config["port"],
                    calling_format=s3_connection.OrdinaryCallingFormat(),
                )
                self._bucket = self._client.get_bucket(self.config["bucket"])
            else:
                scheme = "https" if self.config["is_secure"] else "http"
                endpoint_url = f"{scheme}://{self.config['host']}:{self.config['port']}"
                self._client = boto3.client(
                    "s3",
                    aws_access_key_id=self.config["access_key"],
                    aws_secret_access_key=self.config["secret_key"],
                    endpoint_url=endpoint_url,
                    config=Config(s3={"addressing_style": "path"}),
                )
                self._bucket = _Boto3Bucket(self._client, self.config["bucket"])
        except Exception:
            log("CephAdapter connect error",
                params={log_const.KEY_NAME: log_const.HANDLED_EXCEPTION_VALUE},
                level="ERROR",
                exc_info=True)
            monitoring.got_counter("ceph_connection_exception")
            raise

    @property
    def _handled_exception(self):
        return _CEPH_EXCEPTIONS

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
