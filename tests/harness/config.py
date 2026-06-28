"""
dann-specs Test Configuration Loader

Sensitive data lives in the WORKSPACE ROOT (outside the git-tracked project/ folder).
Example location: ~/Dev/dann-specs/local/llm-providers.json
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

def find_workspace_root(start_path: Path) -> Optional[Path]:
    """
    Walk up from the test runner until we find a folder that contains
    'local/' or 'conversations/' (markers of the workspace root).
    """
    current = start_path.resolve()
    for _ in range(6):  # safety limit
        if (current / "local").is_dir() or (current / "conversations").is_dir():
            return current
        current = current.parent
    return None

def load_llm_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load LLM provider configuration.
    Priority:
      1. Explicit --config path
      2. <workspace_root>/local/llm-providers.json
      3. Fall back to environment variables (single provider)
    """
    if config_path and config_path.exists():
        with open(config_path) as f:
            return json.load(f)

    # Try to auto-detect workspace root
    workspace = find_workspace_root(Path(__file__))
    if workspace:
        candidate = workspace / "local" / "llm-providers.json"
        if candidate.exists():
            with open(candidate) as f:
                return json.load(f)

    # Fallback: single provider from env
    base_url = (
        os.getenv("LLM_BASE_URL") or
        os.getenv("OPENAI_BASE_URL") or
        "http://localhost:8080/v1"
    )
    api_key = (
        os.getenv("LLM_API_KEY") or
        os.getenv("OPENAI_API_KEY") or
        ""
    )
    model = os.getenv("LLM_MODEL", "local")

    # If still no key, try a common llama.cpp default location
    if not api_key:
        api_key = os.getenv("LLAMA_API_KEY", "")

    return {
        "default_provider": "env",
        "providers": {
            "env": {
                "type": "openai-compatible",
                "base_url": base_url,
                "api_key": api_key,
                "model": model
            }
        }
    }

def get_provider(config: Dict[str, Any], provider_name: Optional[str] = None) -> Dict[str, Any]:
    """Get a specific provider config."""
    providers = config.get("providers", {})
    name = provider_name or config.get("default_provider", "env")
    if name not in providers:
        raise ValueError(f"Provider '{name}' not found. Available: {list(providers.keys())}")
    return providers[name]
