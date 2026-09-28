"""Task-level model selection: no paid requests and no user database writes."""
import asyncio
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient
from app.core import db, llm, model_selection as models, orchestrator as orch
from app.main import app

SETTINGS = SimpleNamespace(llm_model='mimo-v2.6-flash', llm_model_core='mimo-v2.6-pro',
                           llm_model_aux='mimo-v2.6-flash', llm_model_fast='mimo-v2.6-flash')


class SelectionTests(unittest.TestCase):
    def setUp(self):
        self.scope = patch.object(models, 'get_settings', return_value=SETTINGS)
        self.scope.start()
        self.addCleanup(self.scope.stop)

    def test_catalog_and_rejection_at_http_boundary(self):
        with TestClient(app) as client:
            response = client.get('/api/models')
            self.assertEqual(response.status_code, 200)
            catalog = response.json()
            enabled = [m['id'] for m in catalog['options'] if m['available']]
            self.assertEqual(enabled, ['auto', 'mimo-v2.6-pro', 'mimo-v2.6-flash'])
            self.assertNotIn('key', response.text.lower())
            with patch.object(orch, '_clarify_questions') as paid:
                for model in ['arbitrary-model', 'mimo-v2.6-pro-ultraspeed']:
                    rejected = client.post('/api/tasks', json={'query': 'test', 'model': model})
                    self.assertEqual(rejected.status_code, 422)
                paid.assert_not_called()

    def test_selection_persists_through_clarification_and_cannot_be_replaced_by_answers(self):
        local = threading.local()
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(db, '_DB_PATH', Path(directory) / 'selection.db'), \
             patch.object(db, '_LOCAL', local), patch.object(db, '_SCHEMA_READY', False), \
             patch.object(orch, '_clarify_questions', side_effect=lambda _: [models.resolve_model('default')]):
            try:
                created = orch.create_task('test', mode='quick', model='mimo-v2.6-pro')
                self.assertEqual(created['clarifyQuestions'], ['mimo-v2.6-pro'])
                orch.submit_clarify(created['taskId'], {'focus': ['pricing'], '_model': 'untrusted', '_mode': 'expert'})
                task = db.get_task(created['taskId'])
                self.assertEqual(task['clarifications'], {'focus': ['pricing'], '_model': 'mimo-v2.6-pro', '_mode': 'quick'})
                self.assertEqual(models.resolve_model('default'), 'default')
            finally:
                if hasattr(local, 'conn'):
                    local.conn.close()

    def test_manual_model_overrides_both_chat_and_stream_and_is_restored(self):
        requests = []
        def complete(**kwargs):
            requests.append(kwargs['model'])
            if kwargs.get('stream'):
                return [SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content='ok'))])]
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='ok'))], usage=None)
        client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=complete)))
        with patch.object(llm, '_get_client', return_value=client), patch.object(llm, 'get_settings', return_value=SETTINGS):
            with models.model_scope('mimo-v2.6-pro'):
                llm.chat([], model='mimo-v2.6-flash')
                self.assertEqual(list(llm.chat_stream([])), ['ok'])
            llm.chat([], model='mimo-v2.6-flash')
        self.assertEqual(requests, ['mimo-v2.6-pro', 'mimo-v2.6-pro', 'mimo-v2.6-flash'])

    def test_refine_keeps_report_selection(self):
        report = {'sections': [{'id': 'summary', 'paragraphs': []}], 'model_selection': 'mimo-v2.6-flash'}
        with patch.object(db, 'get_report', return_value=report), patch.object(db, 'save_report'), \
             patch.object(orch, 'chat_json', return_value={'paragraphs': ['refined']}) as chat:
            self.assertTrue(orch.refine_section('r', 'summary', ['more detail'])['ok'])
            self.assertEqual(chat.call_args.kwargs['model'], 'mimo-v2.6-flash')


class ConcurrencyTests(unittest.IsolatedAsyncioTestCase):
    async def test_concurrent_streams_and_worker_threads_keep_their_own_models(self):
        async def fake_pipeline(task_id, sub_id=''):
            for _ in range(2):
                await asyncio.sleep(0)
                yield await asyncio.to_thread(models.resolve_model, 'auto-tier')
        async def consume(selection):
            events = []
            async for event in orch.run_pipeline(selection):
                self.assertEqual(models.resolve_model('consumer'), 'consumer')
                events.append(event)
            return events
        with patch.object(models, 'get_settings', return_value=SETTINGS), \
             patch.object(db, 'get_task', side_effect=lambda tid: {'clarifications': {'_model': tid}}), \
             patch('builtins.anext', None, create=True), \
             patch.object(orch, '_run_pipeline', fake_pipeline):
            results = await asyncio.gather(consume('mimo-v2.6-pro'), consume('mimo-v2.6-flash'), consume('auto'))
            self.assertEqual(results, [['mimo-v2.6-pro'] * 2, ['mimo-v2.6-flash'] * 2, ['auto-tier'] * 2])
            stream = orch.run_pipeline('mimo-v2.6-pro')
            await stream.__anext__()
            await stream.aclose()
            self.assertEqual(models.resolve_model('after-close'), 'after-close')

    async def test_failed_stream_does_not_leak_model(self):
        async def fail(task_id, sub_id=''):
            yield models.resolve_model('default')
            raise RuntimeError('simulated failure')
        with patch.object(models, 'get_settings', return_value=SETTINGS), \
             patch.object(db, 'get_task', return_value={'clarifications': {'_model': 'mimo-v2.6-pro'}}), \
             patch.object(orch, '_run_pipeline', fail):
            with self.assertRaisesRegex(RuntimeError, 'simulated failure'):
                async for _ in orch.run_pipeline('task'):
                    pass
            self.assertEqual(models.resolve_model('default'), 'default')
