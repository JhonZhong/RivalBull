"""通过真实 OpenAI SDK 和本地 HTTP 模拟验证协议，不调用付费服务。"""
import json
import os
import unittest
from unittest.mock import patch

import httpx
from openai import OpenAI

from app.core import llm
from app.core.config import Settings


class ConfigurationTests(unittest.TestCase):
    def test_mimo_environment_overrides_legacy_names(self):
        with patch.dict(os.environ, {
            "LLM_API_KEY": "test-only-key", "ZHIPU_API_KEY": "legacy-key",
            "LLM_BASE_URL": "https://token-plan-cn.xiaomimimo.com/v1",
            "LLM_MODEL": "mimo-v2.6-flash", "LLM_MODEL_CORE": "mimo-v2.6-pro",
            "LLM_MODEL_AUX": "mimo-v2.6-flash", "LLM_MODEL_FAST": "mimo-v2.6-flash",
        }, clear=True):
            settings = Settings(_env_file=None)
        self.assertEqual(settings.llm_api_key, "test-only-key")
        self.assertEqual(settings.llm_model_core, "mimo-v2.6-pro")
        self.assertEqual(settings.llm_model_fast, "mimo-v2.6-flash")
        self.assertTrue(settings.llm_configured)
        self.assertNotIn("test-only-key", repr(settings))

    def test_legacy_environment_still_works(self):
        with patch.dict(os.environ, {
            "ZHIPU_API_KEY": "legacy-key", "ZHIPU_MODEL": "glm-5.1",
            "ZHIPU_BASE_URL": "https://legacy.example/v1",
        }, clear=True):
            settings = Settings(_env_file=None)
        self.assertEqual(settings.llm_api_key, "legacy-key")
        self.assertEqual(settings.llm_base_url, "https://legacy.example/v1")

    def test_missing_key_does_not_create_client(self):
        with patch.dict(os.environ, {"LLM_API_KEY": "  "}, clear=True):
            settings = Settings(_env_file=None)
        with patch.object(llm, "get_settings", return_value=settings), patch.object(llm, "OpenAI") as client:
            with self.assertRaisesRegex(llm.LLMNotConfigured, "LLM_API_KEY"):
                llm._get_client()
            client.assert_not_called()


class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.requests = []
        self.client = OpenAI(
            api_key="test-only-key", base_url="https://mimo.example/v1", max_retries=0,
            http_client=httpx.Client(transport=httpx.MockTransport(self.respond)),
        )
        self.patcher = patch.object(llm, "_get_client", return_value=self.client)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
        self.addCleanup(self.client.close)

    def respond(self, request):
        body = json.loads(request.content)
        self.requests.append(body)
        self.assertEqual(request.url.path, "/v1/chat/completions")
        if body.get("stream"):
            chunks = [
                {"choices": []},
                {"choices": [{"index": 0, "delta": {"content": "ready"}}]},
            ]
            content = "".join("data: " + json.dumps(c) + "\n\n" for c in chunks)
            return httpx.Response(200, headers={"Content-Type": "text/event-stream"},
                                  content=content + "data: [DONE]\n\n")
        return httpx.Response(200, json={
            "id": "test", "object": "chat.completion", "created": 0,
            "model": body["model"],
            "choices": [{"index": 0, "finish_reason": "stop",
                         "message": {"role": "assistant", "content": '{"ok": true}'}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 2, "total_tokens": 3},
        })

    def test_mimo_models_send_completion_budget_and_disable_thinking(self):
        for model in ("mimo-v2.6-pro", "mimo-v2.6-flash", "mimo-v2.6-pro-ultraspeed"):
            with self.subTest(model=model):
                result = llm.chat_json([{"role": "user", "content": "JSON please"}],
                                       model=model, max_tokens=512)
                self.assertEqual(result, {"ok": True})
                body = self.requests[-1]
                self.assertEqual(body["model"], model)
                self.assertEqual(body["max_completion_tokens"], 512)
                self.assertNotIn("max_tokens", body)
                self.assertEqual(body["thinking"], {"type": "disabled"})

    def test_stream_uses_same_mimo_protocol_and_skips_usage_only_chunks(self):
        result = list(llm.chat_stream([{"role": "user", "content": "hello"}],
                                      model="mimo-v2.6-flash", max_tokens=128))
        self.assertEqual(result, ["ready"])
        self.assertEqual(self.requests[-1]["max_completion_tokens"], 128)
        self.assertEqual(self.requests[-1]["thinking"], {"type": "disabled"})

    def test_glm_keeps_existing_token_parameter(self):
        llm.chat([{"role": "user", "content": "hello"}], model="glm-5.1", max_tokens=128)
        self.assertEqual(self.requests[-1]["max_tokens"], 128)
        self.assertNotIn("max_completion_tokens", self.requests[-1])


if __name__ == "__main__":
    unittest.main()
