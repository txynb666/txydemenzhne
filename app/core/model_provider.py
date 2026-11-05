"""Shared OpenAI-compatible clients and safe, actionable provider errors."""
import os
from urllib.parse import urlsplit

from openai import OpenAI, APIConnectionError, APITimeoutError


class ModelConfigurationError(ValueError):
    pass


def settings(kind="llm"):
    prefix = "EMBED" if kind == "embed" else "LLM"
    llm_url = os.getenv("LLM_BASE_URL", "").strip() or "https://api.deepseek.com/v1"
    url = os.getenv(prefix + "_BASE_URL", "").strip() or llm_url
    local = urlsplit(url).hostname in {"localhost", "127.0.0.1", "host.docker.internal", "ollama"}
    key = os.getenv(prefix + "_API_KEY", "").strip() or os.getenv("LLM_API_KEY", "").strip()
    if local:
        key = key or "ollama"
    if not key or key in {"EMPTY", "sk-your-key-here"}:
        raise ModelConfigurationError(f"请在 .env 中填写 {prefix}_API_KEY；本地 Ollama 可填写 ollama")
    parts = urlsplit(url)
    if parts.scheme not in {"http", "https"} or not parts.hostname or parts.username or parts.password:
        raise ModelConfigurationError(f"{prefix}_BASE_URL 必须是有效的 HTTP(S) 接口地址，不要在地址中放密钥")
    default_model = "BAAI/bge-m3" if kind == "embed" else "deepseek-chat"
    model = os.getenv(prefix + "_MODEL", "").strip() or default_model
    return {"api_key": key, "base_url": url.rstrip("/"), "model": model}


def client(kind="llm"):
    cfg = settings(kind)
    # Avoid long automatic retries, especially for local demo deployments.
    return OpenAI(api_key=cfg["api_key"], base_url=cfg["base_url"],
                  timeout=120.0, max_retries=0)


def model_name(kind="llm"):
    return settings(kind)["model"]


def provider_error(exc, kind="llm"):
    """Never return raw provider responses: they may contain credentials or prompts."""
    label = "向量模型" if kind == "embed" else "对话模型"
    if isinstance(exc, ModelConfigurationError):
        return str(exc)
    if isinstance(exc, APITimeoutError):
        return f"{label}请求超时；本地模型首次加载较慢，请稍后重试"
    if isinstance(exc, APIConnectionError):
        return f"无法连接{label}；请检查接口地址、网络及 Ollama 是否启动（Docker 内使用 host.docker.internal）"
    status = getattr(exc, "status_code", None)
    hints = {
        400: "请求不被支持，请检查模型名称及工具调用支持情况",
        401: "API 密钥无效，请检查 .env 中对应的 API_KEY",
        402: "账户余额不足；请充值，或按 README 切换免费本地 Ollama 模型",
        403: "访问被拒绝，请检查账户及模型使用权限",
        404: "接口或模型不存在；请检查 BASE_URL 和 MODEL，本地模型需先 ollama pull",
        429: "请求额度或速率受限，请检查服务商配额并稍后重试",
    }
    return f"{label}：{hints.get(status, '服务调用失败，请运行模型自检查看故障类别')}"
