"""Public model catalog and request-local selection, shared by every LLM call.

ContextVar follows asyncio tasks and asyncio.to_thread without changing global
settings. Resuming a pipeline scopes each generator step, so closing an SSE
stream cannot leave a model override in its caller's context.
"""
from contextlib import contextmanager
from contextvars import ContextVar

from app.core.config import get_settings

_selection: ContextVar[str] = ContextVar("rivalbull_model", default="auto")


def model_catalog() -> dict:
    settings = get_settings()
    tiers = {"core": settings.llm_model_core, "aux": settings.llm_model_aux,
             "fast": settings.llm_model_fast}
    ids = list(dict.fromkeys([*tiers.values(), settings.llm_model]))
    labels = {"mimo-v2.6-pro": "MiMo-V2.6-Pro", "mimo-v2.6-flash": "MiMo-V2.6-Flash",
              "mimo-v2.6-pro-ultraspeed": "MiMo-V2.6-Pro-UltraSpeed"}
    options = [{"id": "auto", "label": "自动分工", "available": True,
                "description": "核心分析使用主力模型，辅助与整理使用轻量模型"}]
    options += [{"id": mid, "label": labels.get(mid.lower(), mid), "available": True,
                 "description": "本次调研全程使用此模型"} for mid in ids if mid]
    if not any("ultraspeed" in mid.lower() for mid in ids):
        options.append({"id": "mimo-v2.6-pro-ultraspeed", "label": "MiMo-V2.6-Pro-UltraSpeed",
                        "available": False, "description": "当前服务未启用，需另行配置支持此模型的服务"})
    return {"options": options, "tiers": tiers}


def validate_selection(selection: str) -> str:
    allowed = {item["id"] for item in model_catalog()["options"] if item["available"]}
    if selection not in allowed:
        raise ValueError("所选模型未在当前服务中启用，请刷新模型列表后重试。")
    return selection


def resolve_model(default: str) -> str:
    selected = _selection.get()
    return default if selected == "auto" else selected


@contextmanager
def model_scope(selection: str):
    token = _selection.set(validate_selection(selection))
    try:
        yield
    finally:
        _selection.reset(token)
