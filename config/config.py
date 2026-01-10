from __future__ import annotations
from enum import Enum
import os
from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field, model_validator


class Provider(str, Enum):
    OLLAMA = "ollama"
    GEMINI = "gemini"
    MISTRAL = "mistral"
    OPENAI = "openai"
    GROQ = "groq"


# Provider configurations
PROVIDER_CONFIG = {
    Provider.OLLAMA: {
        "base_url": "http://localhost:11434/v1",
        "default_model": "qwen2.5-coder:7b",
        "vision_model": "llava:7b",
        "env_key": "OLLAMA_API_KEY",
        "default_key": "ollama",
        "models": [
            {"name": "qwen2.5-coder:7b", "desc": "Best for Coding", "type": "coding"},
            {"name": "qwen2.5-coder:14b", "desc": "Better Coding, Slower", "type": "coding"},
            {"name": "codellama:7b", "desc": "Good for Code", "type": "coding"},
            {"name": "deepseek-coder:6.7b", "desc": "Fast Coding", "type": "coding"},
            {"name": "llama3:8b", "desc": "General Purpose", "type": "general"},
            {"name": "mistral:7b", "desc": "Fast & Smart", "type": "general"},
            {"name": "llava:7b", "desc": "Vision + Text", "type": "vision"},
            {"name": "llava:13b", "desc": "Better Vision", "type": "vision"},
        ],
    },
    Provider.GEMINI: {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "default_model": "gemini-2.0-flash",
        "vision_model": "gemini-2.0-flash",
        "env_key": "GEMINI_API_KEY",
        "models": [
            {"name": "gemini-2.0-flash", "desc": "Best & Fast ⭐", "type": "coding"},
            {"name": "gemini-1.5-flash", "desc": "Fast, Good for Code", "type": "coding"},
            {"name": "gemini-1.5-pro", "desc": "Most Capable", "type": "general"},
        ],
    },
    Provider.MISTRAL: {
        "base_url": "https://api.mistral.ai/v1",
        "default_model": "open-mistral-nemo",
        "vision_model": "pixtral-12b-2409",
        "env_key": "MISTRAL_API_KEY",
        "models": [
            # Free/Open models that work without special access
            {"name": "open-mistral-nemo", "desc": "Free Open Source ⭐", "type": "coding"},
            {"name": "open-mistral-7b", "desc": "Free 7B Model", "type": "general"},
            {"name": "open-mixtral-8x7b", "desc": "Free Mixtral", "type": "general"},
            # Paid models (need subscription)
            {"name": "mistral-small-latest", "desc": "Paid - Fast", "type": "coding"},
            {"name": "mistral-large-latest", "desc": "Paid - Powerful", "type": "general"},
            {"name": "pixtral-12b-2409", "desc": "Vision Model", "type": "vision"},
        ],
    },
    Provider.OPENAI: {
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o-mini",
        "vision_model": "gpt-4o-mini",
        "env_key": "OPENAI_API_KEY",
        "models": [
            {"name": "gpt-4o", "desc": "Best Overall ⭐", "type": "general"},
            {"name": "gpt-4o-mini", "desc": "Fast & Cheap, Good for Code", "type": "coding"},
            {"name": "gpt-4-turbo", "desc": "Powerful, Expensive", "type": "general"},
            {"name": "gpt-3.5-turbo", "desc": "Cheapest, Basic", "type": "general"},
            {"name": "gpt-4o", "desc": "Vision Support", "type": "vision"},
        ],
    },
    Provider.GROQ: {
        "base_url": "https://api.groq.com/openai/v1",
        "default_model": "llama-3.3-70b-versatile",
        "vision_model": "llama-3.2-90b-vision-preview",
        "env_key": "GROQ_API_KEY",
        "models": [
            {"name": "llama-3.3-70b-versatile", "desc": "Best Overall ⭐ Ultra Fast", "type": "coding"},
            {"name": "llama-3.1-8b-instant", "desc": "Fastest, Good for Code", "type": "coding"},
            {"name": "llama-3.2-90b-vision-preview", "desc": "Vision + Text", "type": "vision"},
            {"name": "mixtral-8x7b-32768", "desc": "Good Balance", "type": "general"},
            {"name": "gemma2-9b-it", "desc": "Google's Model", "type": "general"},
        ],
    },
}


class ModelConfig(BaseModel):
    name: str = "qwen2.5-coder:7b"
    vision_model: str = "llava:7b"
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    context_window: int = 32_000
    provider: Provider = Provider.OLLAMA


class ShellEnvironmentPolicy(BaseModel):
    ignore_default_excludes: bool = False
    exclude_patterns: list[str] = Field(
        default_factory=lambda: ["*KEY*", "*TOKEN*", "*SECRET*"]
    )
    set_vars: dict[str, str] = Field(default_factory=dict)


class MCPServerConfig(BaseModel):
    enabled: bool = True
    startup_timeout_sec: float = 10

    # stdio transport
    command: str | None = None
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    cwd: Path | None = None

    # http/sse transport
    url: str | None = None

    @model_validator(mode="after")
    def validate_transport(self) -> MCPServerConfig:
        has_command = self.command is not None
        has_url = self.url is not None

        if not has_command and not has_url:
            raise ValueError(
                "MCP Server must have either 'command' (stdio) or 'url' (http/sse)"
            )

        if has_command and has_url:
            raise ValueError(
                "MCP Server cannot have both 'command' (stdio) and 'url' (http/sse)"
            )

        return self


class ApprovalPolicy(str, Enum):
    ON_REQUEST = "on-request"
    ON_FAILURE = "on-failure"
    AUTO = "auto"
    AUTO_EDIT = "auto-edut"
    NEVER = "never"
    YOLO = "yolo"


class HookTrigger(str, Enum):
    BEFORE_AGENT = "before_agent"
    AFTER_AGENT = "after_agent"
    BEFORE_TOOL = "before_tool"
    AFTER_TOOL = "after_tool"
    ON_ERROR = "on_error"


class HookConfig(BaseModel):
    name: str
    trigger: HookTrigger
    command: str | None = None  # python3 tests.py
    script: str | None = None  # *.sh
    timeout_sec: float = 30
    enabled: bool = True

    @model_validator(mode="after")
    def validate_hook(self) -> HookConfig:
        if not self.command and not self.script:
            raise ValueError("Hook must either have 'command' or 'script'")
        return self


class Config(BaseModel):
    model: ModelConfig = Field(default_factory=ModelConfig)
    cwd: Path = Field(default_factory=Path.cwd)
    shell_environment: ShellEnvironmentPolicy = Field(
        default_factory=ShellEnvironmentPolicy
    )
    hooks_enabled: bool = False
    hooks: list[HookConfig] = Field(default_factory=list)
    approval: ApprovalPolicy = ApprovalPolicy.ON_REQUEST
    max_turns: int = 200
    mcp_servers: dict[str, MCPServerConfig] = Field(default_factory=dict)

    allowed_tools: list[str] | None = Field(
        None,
        description="If set, only these tools will be available to the agent",
    )

    developer_instructions: str | None = None
    user_instructions: str | None = None

    debug: bool = False
    
    # Image path for vision model support
    image_path: str | None = None

    @property
    def provider(self) -> Provider:
        return self.model.provider

    @provider.setter
    def provider(self, value: Provider) -> None:
        self.model.provider = value

    @property
    def api_key(self) -> str | None:
        # First check provider-specific env var
        provider_config = PROVIDER_CONFIG.get(self.model.provider, {})
        env_key = provider_config.get("env_key", "API_KEY")
        key = os.environ.get(env_key)
        
        # Fallback to generic API_KEY
        if not key:
            key = os.environ.get("API_KEY")
        
        # For Ollama, use default key if not set
        if not key and self.model.provider == Provider.OLLAMA:
            key = provider_config.get("default_key", "ollama")
        
        return key

    @property
    def base_url(self) -> str | None:
        # First check env var
        url = os.environ.get("BASE_URL")
        if url:
            return url
        
        # Use provider default
        provider_config = PROVIDER_CONFIG.get(self.model.provider, {})
        return provider_config.get("base_url")

    @property
    def model_name(self) -> str:
        return self.model.name

    @model_name.setter
    def model_name(self, value: str) -> None:
        self.model.name = value

    @property
    def vision_model_name(self) -> str:
        return self.model.vision_model

    @property
    def temperature(self) -> float:
        return self.model.temperature

    @model_name.setter
    def temperature(self, value: str) -> None:
        self.model.temperature = value

    def set_provider(self, provider: Provider, api_key: str | None = None) -> None:
        """Set provider and optionally API key."""
        self.model.provider = provider
        provider_config = PROVIDER_CONFIG.get(provider, {})
        
        # Set default models for provider
        self.model.name = provider_config.get("default_model", self.model.name)
        self.model.vision_model = provider_config.get("vision_model", self.model.vision_model)
        
        # Set API key in environment if provided
        if api_key:
            env_key = provider_config.get("env_key", "API_KEY")
            os.environ[env_key] = api_key
            os.environ["API_KEY"] = api_key

    def validate(self) -> list[str]:
        errors: list[str] = []

        if not self.api_key:
            provider_config = PROVIDER_CONFIG.get(self.model.provider, {})
            env_key = provider_config.get("env_key", "API_KEY")
            errors.append(f"No API key found. Set {env_key} environment variable")

        if not self.cwd.exists():
            errors.append(f"Working directory does not exist: {self.cwd}")

        return errors

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")
