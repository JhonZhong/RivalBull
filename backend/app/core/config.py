"""全局配置：从环境变量 / .env 读取，不硬编码密钥（第 16.4 章）。"""
import os
from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# 用绝对路径定位 backend/.env，避免因启动工作目录不同而读不到密钥。
# config.py 位于 backend/app/core/，向上三级即 backend/。
_BACKEND_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
_ENV_FILE = os.path.join(_BACKEND_DIR, ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE, env_file_encoding="utf-8", extra="ignore"
    )

    # OpenAI 兼容服务：新部署使用 LLM_*，同时兼容旧的 ZHIPU_* 配置。
    llm_api_key: str = Field(
        default="", repr=False,
        validation_alias=AliasChoices("LLM_API_KEY", "MIMO_API_KEY", "ZHIPU_API_KEY"),
    )
    llm_model: str = Field(
        default="mimo-v2.6-flash", validation_alias=AliasChoices("LLM_MODEL", "ZHIPU_MODEL"),
    )
    llm_model_core: str = Field(
        default="mimo-v2.6-pro", validation_alias=AliasChoices("LLM_MODEL_CORE", "ZHIPU_MODEL_CORE"),
    )
    llm_model_aux: str = Field(
        default="mimo-v2.6-flash", validation_alias=AliasChoices("LLM_MODEL_AUX", "ZHIPU_MODEL_AUX"),
    )
    llm_model_fast: str = Field(
        default="mimo-v2.6-flash", validation_alias=AliasChoices("LLM_MODEL_FAST", "ZHIPU_MODEL_FAST"),
    )
    llm_base_url: str = Field(
        default="https://token-plan-cn.xiaomimimo.com/v1",
        validation_alias=AliasChoices("LLM_BASE_URL", "ZHIPU_BASE_URL"),
    )
    # 单次 LLM 调用超时（秒）与自动重试次数，避免请求卡死拖垮整个服务。
    # analyze 等重型 JSON 调用（claims+对比+定价+五力+趋势一次产出）在大 max_tokens
    # 下耗时较长，180s 给足余量；max_retries 设 1，避免超时后再叠加 2 次重试（最坏 3×timeout）。
    llm_timeout: float = 180.0
    llm_max_retries: int = 1

    # 搜索 API（博查 Bocha Web Search：https://open.bocha.cn 获取 key）
    bocha_api_key: str = ""
    bocha_base_url: str = "https://api.bocha.cn/v1"
    # 单次搜索超时（秒）
    search_timeout: float = 30.0
    # 兼容旧字段（已弃用，不再使用）
    serpapi_key: str = ""
    bing_search_key: str = ""

    # 平台采集
    douyin_cookie: str = ""
    xhs_cookie: str = ""
    bilibili_cookie: str = ""

    # 服务
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    frontend_origin: str = "http://localhost:5173"
    enable_demo_fallback: bool = True

    @property
    def llm_configured(self) -> bool:
        return bool(self.llm_api_key.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()
