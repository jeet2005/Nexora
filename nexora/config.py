"""Global configuration for Nexora."""

from __future__ import annotations

import os


class NexoraConfig:
    """Thread-safe configuration for Nexora."""

    def __init__(self):
        self._config = {
            "llm_provider": os.environ.get("NEXORA_LLM_PROVIDER", "ollama"),
            "llm_model": os.environ.get("NEXORA_LLM_MODEL", "llama3"),
            "openai_api_key": os.environ.get("OPENAI_API_KEY", ""),
            "ollama_base_url": os.environ.get(
                "OLLAMA_BASE_URL", "http://localhost:11434"
            ),
        }

    def set(self, **kwargs) -> None:
        """Set configuration parameters.

        Args:
            **kwargs: Configuration keys and values to update.

        Example:
            `nexora.config.set(llm_provider="ollama", llm_model="llama3")`
        """
        for k, v in kwargs.items():
            if k in self._config:
                self._config[k] = v
            else:
                raise ValueError(f"Unknown configuration key: {k}")

    def get(self, key: str, default=None) -> str | None:
        """Get a configuration parameter."""
        return self._config.get(key, default)


# Global singleton
config = NexoraConfig()
