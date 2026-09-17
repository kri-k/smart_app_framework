import subprocess
import sys
import unittest


class TestLegacyImports(unittest.TestCase):
    @unittest.skipIf(sys.version_info < (3, 12), "imp is still part of Python < 3.12")
    def test_boto_import_does_not_leave_global_imp_stub(self):
        # Use a fresh interpreter: Settings imports this adapter during discovery.
        result = subprocess.run(
            [sys.executable, "-c", """
import importlib.util
import sys
from core.db_adapter.ceph.ceph_adapter import boto
assert 'imp' not in sys.modules
assert importlib.util.find_spec('imp') is None
connection = boto.connect_s3(
    aws_access_key_id='test', aws_secret_access_key='test',
    host='localhost', port=9000, is_secure=False,
)
assert 'AWSAccessKeyId=test' in connection.generate_url(60, 'GET', bucket='bucket', key='key')
connection.close()
"""], capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
