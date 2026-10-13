"""
Deterministic placeholder adapter. External model providers are not implemented.
"""
from typing import Dict, Any, Optional
from .base import PHIGuard


class MockLLM:
    def __init__(self, system_name: str = "Ecg Axis Calculator"):
        self.system_name = system_name

    def invoke(self, prompt: str) -> str:
        PHIGuard.assert_no_phi(prompt)
        return (f"[{self.system_name} Mock adapter] No clinical or scientific verification "
                f"was performed. Query excerpt: '{prompt[:60]}...'.")


class LLMFactory:
    """Return the mock adapter; external LLM providers are not implemented."""

    @staticmethod
    def create(provider: str = "mock", system_name: str = "Ecg Axis Calculator"):
        prov = str(provider).lower()
        if prov in ["mock", "deterministic", "test"]:
            return MockLLM(system_name)
        elif prov in ["ollama", "local"]:
            return MockLLM(system_name)
        elif prov in ["claude", "anthropic"]:
            return MockLLM(system_name)
        elif prov in ["openai", "gpt4"]:
            return MockLLM(system_name)
        return MockLLM(system_name)
