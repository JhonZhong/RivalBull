"""在独立进程中验证两套 app 包，避免导入缓存掩盖部署镜像差异。"""
import subprocess
import sys
import unittest
from pathlib import Path


class EntrypointContractTests(unittest.TestCase):
    def check_entrypoint(self, entrypoint):
        probe = Path(__file__).with_name('entrypoint_contract_probe.py')
        result = subprocess.run([sys.executable, '-B', str(probe), entrypoint],
                                capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_local_backend(self):
        self.check_entrypoint('backend')

    def test_deployment_api(self):
        self.check_entrypoint('api')
