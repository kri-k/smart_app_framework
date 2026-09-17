import os
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import unittest


class TestWsgiTemplate(unittest.TestCase):
    def _check_generated_app(self, custom_postprocessor):
        # A fresh interpreter isolates app_config, cached settings, signal handlers,
        # monitoring singletons and the event loop from the rest of the suite.
        script = textwrap.dedent("""
            import os
            import sys

            from smart_kit.management.smart_kit_manager import CreateAppCommand
            from smart_kit.start_points.postprocess import PostprocessMainLoop

            CreateAppCommand().execute("wsgi_test_app")
            os.chdir("wsgi_test_app")
            sys.path.insert(0, os.getcwd())
            import app_config

            expected_postprocessor = PostprocessMainLoop
            if sys.argv[1] == "custom":
                class CustomPostprocessor(PostprocessMainLoop):
                    pass
                app_config.POSTPROCESSOR_MAIN_LOOP = CustomPostprocessor
                expected_postprocessor = CustomPostprocessor

            from wsgi import create_app
            app = create_app()
            try:
                assert type(app.postprocessor) is expected_postprocessor
                status = []
                body = b"".join(app(
                    {"PATH_INFO": "/health"},
                    lambda response_status, headers: status.append(response_status),
                ))
                assert status == ["200 OK"], status
                assert body == b"ok", body
            finally:
                app.loop.close()
        """)
        env = os.environ.copy()
        for name in ("SMART_KIT_APP_CONFIG", "STATIC_PATH", "CONFIGS_PATH", "SECRET_PATH",
                     "REFERENCES_PATH", "STATIC_CLASSIFIERS_PATH", "STATIC_CLASSIFIERS_DATA_PATH"):
            env.pop(name, None)
        env["PYTHONPATH"] = str(Path(__file__).resolve().parents[3])
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, "-c", script, "custom" if custom_postprocessor else "default"],
                cwd=directory, env=env, capture_output=True, text=True, timeout=60,
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_generated_wsgi_app_uses_default_postprocessor(self):
        self._check_generated_app(custom_postprocessor=False)

    def test_generated_wsgi_app_uses_configured_postprocessor(self):
        self._check_generated_app(custom_postprocessor=True)
