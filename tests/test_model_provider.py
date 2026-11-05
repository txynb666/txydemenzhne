import pathlib
import sys
from types import SimpleNamespace

import httpx
import pytest
from openai import APIStatusError

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from app.core import model_provider as provider


@pytest.fixture(autouse=True)
def clean_settings(monkeypatch):
    for prefix in ("LLM", "EMBED"):
        for suffix in ("API_KEY", "BASE_URL", "MODEL"):
            monkeypatch.delenv(f"{prefix}_{suffix}", raising=False)


def test_blank_embedding_values_fall_back(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "test-secret")
    monkeypatch.setenv("LLM_BASE_URL", "https://example.com/v1")
    monkeypatch.setenv("EMBED_API_KEY", "  ")
    monkeypatch.setenv("EMBED_BASE_URL", "")
    assert provider.settings("embed")["api_key"] == "test-secret"
    assert provider.settings("embed")["base_url"] == "https://example.com/v1"


def test_local_model_needs_no_real_key(monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "http://host.docker.internal:11434/v1")
    monkeypatch.setenv("LLM_MODEL", "qwen3:4b")
    assert provider.settings()["api_key"] == "ollama"
    assert provider.model_name() == "qwen3:4b"


def test_missing_cloud_key_gives_actionable_message():
    with pytest.raises(provider.ModelConfigurationError, match="LLM_API_KEY"):
        provider.settings()


@pytest.mark.parametrize("status,hint", [(401, "密钥"), (402, "余额不足"),
                                        (404, "不存在"), (429, "配额")])
def test_provider_errors_do_not_leak_secrets(status, hint):
    exc = APIStatusError("secret-in-raw-error", response=httpx.Response(
        status, request=httpx.Request("POST", "https://example.com")), body=None)
    message = provider.provider_error(exc)
    assert hint in message
    assert "secret-in-raw-error" not in message


def test_harness_emits_balance_error(monkeypatch):
    from app.agents import harness
    monkeypatch.setattr(harness.agent_trace, "log_step", lambda *a, **kw: None)
    monkeypatch.setattr(harness.agent_mod, "get_system_prompt", lambda: "test")
    def failing_client():
        raise APIStatusError("private response", response=httpx.Response(
            402, request=httpx.Request("POST", "https://example.com")), body=None)
    monkeypatch.setattr(harness, "_client", failing_client)
    events = list(harness.run("你好", [], "test"))
    assert events[-1]["type"] == "error"
    assert "余额不足" in events[-1]["message"]


def test_embedding_failure_is_actionable(monkeypatch):
    from app import rag
    def failing_client():
        raise APIStatusError("private", response=httpx.Response(
            401, request=httpx.Request("POST", "https://example.com")), body=None)
    monkeypatch.setattr(rag, "_embed_client", failing_client)
    with pytest.raises(rag.RagError, match="向量模型.*密钥"):
        rag.embed(["就诊"])


def test_embedding_change_invalidates_cached_index(monkeypatch, tmp_path):
    import json
    import numpy as np
    from app import rag
    monkeypatch.setenv("LLM_BASE_URL", "http://localhost:11434/v1")
    monkeypatch.setenv("EMBED_MODEL", "bge-m3")
    (tmp_path / "chunks.json").write_text(json.dumps({"embedding": {
        "base_url": "https://old-provider/v1", "model": "old-model"}}))
    np.save(tmp_path / "vecs.npy", np.zeros((1, 3)))
    monkeypatch.setattr(rag, "INDEX_DIR", tmp_path)
    monkeypatch.setattr(rag, "_retriever", None)
    rebuilt = object()
    monkeypatch.setattr(rag, "_build", lambda: rebuilt)
    assert rag.get_retriever() is rebuilt


def test_chat_sse_returns_actionable_model_error(monkeypatch):
    from fastapi.testclient import TestClient
    from app import main
    def failed_run(*args, **kwargs):
        yield {"type": "error", "message": "对话模型：账户余额不足"}
    monkeypatch.setattr(main.harness, "run", failed_run)
    with TestClient(main.app) as api:
        result = api.post("/chat", json={"question": "就诊需要准备什么"})
    assert result.status_code == 200  # SSE errors are carried inside the stream.
    assert "event: error" in result.text
    assert "账户余额不足" in result.text


def test_retrieval_failure_has_nonzero_error_code(monkeypatch):
    from app import rag
    from app.services import tools
    def failed_retriever():
        raise rag.RagError("EMBED_UNAVAILABLE", "向量模型：API 密钥无效")
    monkeypatch.setattr(rag, "get_retriever", failed_retriever)
    result = tools.search_policy("就诊")
    assert result["ok"] is False
    assert result["code"] == 4002
    assert "密钥" in result["message"]


def test_confirmed_action_still_gets_model_summary(monkeypatch):
    from app.agents import harness
    monkeypatch.setenv("LLM_BASE_URL", "http://localhost:11434/v1")
    monkeypatch.setattr(harness.agent_trace, "take_pending", lambda *a: ({
        "run_id": "test", "action": "create_reimbursement_draft", "arguments": "{}", "conv_id": "test"
    }, None))
    monkeypatch.setattr(harness, "_normalize_draft_args", lambda args, user_id: args)
    monkeypatch.setattr(harness, "_exec_tool", lambda *a: {"ok": True})
    monkeypatch.setattr(harness.agent_mod, "get_system_prompt", lambda: "test")
    reply = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="草稿已生成，请等待审核"))])
    fake = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kw: reply)))
    monkeypatch.setattr(harness, "_client", lambda: fake)
    events = list(harness.resume("token", "test"))
    assert "".join(e["text"] for e in events if e["type"] == "delta") == "草稿已生成，请等待审核"
