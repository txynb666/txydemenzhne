"""Explicit opt-in connectivity test. Makes one small chat and embedding request."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
# Read .env before building clients for native Python startup.
from app.core import config  # noqa: E402,F401
from app.core.model_provider import client, model_name, provider_error  # noqa: E402


def main():
    failed = False
    for kind, label in (("llm", "对话模型"), ("embed", "向量模型")):
        try:
            api = client(kind)
            if kind == "llm":
                from app.services.tools import TOOLS_SPEC
                result = api.chat.completions.create(
                    model=model_name(), messages=[{"role": "user", "content": "你好，请简短回复"}],
                    tools=TOOLS_SPEC, tool_choice="auto", max_tokens=128)
                msg = result.choices[0].message
                if not msg.content and not msg.tool_calls:
                    raise ValueError("empty model response")
            else:
                result = api.embeddings.create(model=model_name(kind), input=["就诊须知"])
                if not result.data or not result.data[0].embedding:
                    raise ValueError("empty embedding response")
            print(f"[OK] {label} ({model_name(kind)})")
        except Exception as exc:
            failed = True
            print(f"[FAIL] {provider_error(exc, kind)} (type={type(exc).__name__}, status={getattr(exc, 'status_code', '-')})")
    return int(failed)


if __name__ == "__main__":
    sys.exit(main())
