"""同一接口契约分别运行于本地/部署入口；只使用临时数据库和模拟模型。"""
import importlib.util
import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
ENTRYPOINT = sys.argv.pop(1)
sys.path.insert(0, str(ROOT / ENTRYPOINT))

from fastapi.testclient import TestClient
from app.core import config, db, model_selection, orchestrator

if ENTRYPOINT == 'api':
    spec = importlib.util.spec_from_file_location('deployment_entry', ROOT / 'api/index.py')
    entry = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(entry)
else:
    from app import main as entry


class HttpContract(unittest.TestCase):
    def test_creation_catalog_persistence_and_rejection(self):
        with patch.dict(os.environ, {}, clear=True):
            settings = config.Settings(_env_file=None)
        local = threading.local()
        # 不启动应用生命周期；所有数据库访问使用临时路径。
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(db, '_DB_PATH', Path(directory) / 'contract.db'), \
             patch.object(db, '_LOCAL', local), patch.object(db, '_SCHEMA_READY', False), \
             patch.object(model_selection, 'get_settings', return_value=settings), \
             patch.object(orchestrator, '_clarify_questions', return_value=[]) as paid:
            client = TestClient(entry.app, raise_server_exceptions=False)
            try:
                catalog = client.get('/api/models')
                self.assertEqual(catalog.status_code, 200)
                self.assertEqual([o['id'] for o in catalog.json()['options'] if o['available']],
                                 ['auto', 'mimo-v2.6-pro', 'mimo-v2.6-flash'])
                for selected in (None, 'auto', 'mimo-v2.6-pro', 'mimo-v2.6-flash'):
                    with self.subTest(model=selected):
                        body = {'query': 'contract test', 'mode': 'quick'}
                        if selected is not None:
                            body['model'] = selected
                        response = client.post('/api/tasks', json=body)
                        self.assertEqual(response.status_code, 200, response.text)
                        task = db.get_task(response.json()['taskId'])
                        self.assertEqual(task['clarifications']['_model'], selected or 'auto')
                paid.reset_mock()
                for selected in ('unknown', 'mimo-v2.6-pro-ultraspeed', None, 123):
                    response = client.post('/api/tasks', json={'query': 'invalid', 'model': selected})
                    self.assertEqual(response.status_code, 422, response.text)
                paid.assert_not_called()
            finally:
                client.close()
                if hasattr(local, 'conn'):
                    local.conn.close()


class ProviderContract(unittest.TestCase):
    def settings(self, env):
        with patch.dict(os.environ, env, clear=True):
            return config.Settings(_env_file=None)

    def assert_legacy_defaults(self, settings):
        self.assertEqual(settings.llm_base_url, 'https://open.bigmodel.cn/api/paas/v4')
        self.assertEqual((settings.llm_model, settings.llm_model_core,
                          settings.llm_model_aux, settings.llm_model_fast),
                         ('glm-5.1', 'glm-5.2', 'glm-5.1', 'glm-z1-air'))

    def test_legacy_key_only(self):
        self.assert_legacy_defaults(self.settings({'ZHIPU_API_KEY': 'synthetic-legacy'}))

    def test_legacy_dotenv(self):
        with tempfile.TemporaryDirectory() as directory:
            envfile = Path(directory) / '.env'
            envfile.write_text('ZHIPU_API_KEY=synthetic-legacy\n', encoding='utf-8')
            with patch.dict(os.environ, {}, clear=True):
                self.assert_legacy_defaults(config.Settings(_env_file=envfile))

    def test_explicit_provider_overrides(self):
        settings = self.settings({'ZHIPU_API_KEY': 'synthetic-legacy',
                                  'ZHIPU_BASE_URL': 'https://legacy.example/v1',
                                  'ZHIPU_MODEL_CORE': 'legacy-core',
                                  'LLM_MODEL_CORE': 'explicit-core'})
        self.assertEqual(settings.llm_base_url, 'https://legacy.example/v1')
        self.assertEqual(settings.llm_model_core, 'explicit-core')
        self.assertEqual(settings.llm_model_fast, 'glm-z1-air')

    def test_modern_keys_take_precedence(self):
        for key in ('LLM_API_KEY', 'MIMO_API_KEY'):
            with self.subTest(key=key):
                settings = self.settings({key: 'synthetic-modern', 'ZHIPU_API_KEY': 'synthetic-legacy'})
                self.assertEqual(settings.llm_api_key, 'synthetic-modern')
                self.assertEqual(settings.llm_base_url, 'https://token-plan-cn.xiaomimimo.com/v1')
                self.assertEqual(settings.llm_model_core, 'mimo-v2.6-pro')

    def test_empty_modern_key_does_not_silently_use_legacy(self):
        settings = self.settings({'LLM_API_KEY': '', 'ZHIPU_API_KEY': 'synthetic-legacy'})
        self.assertFalse(settings.llm_configured)
        self.assertEqual(settings.llm_model, 'mimo-v2.6-flash')

    def test_defaults_without_credentials(self):
        settings = self.settings({})
        self.assertFalse(settings.llm_configured)
        self.assertEqual(settings.llm_model_core, 'mimo-v2.6-pro')


if __name__ == '__main__':
    unittest.main()
