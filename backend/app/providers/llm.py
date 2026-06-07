import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Type, List, Dict
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class LLMProvider(ABC):
    @abstractmethod
    async def generate_structured(self, prompt: str, response_model: Type[BaseModel], **kwargs: Any) -> BaseModel:
        """Enforces Pydantic structured output validation."""
        pass

class MockLLMProvider(LLMProvider):
    def __init__(self, preset_responses: Dict[str, BaseModel] = None):
        self.preset_responses = preset_responses or {}
        self.calls: List[Dict[str, Any]] = []

    async def generate_structured(self, prompt: str, response_model: Type[BaseModel], **kwargs: Any) -> BaseModel:
        self.calls.append({"prompt": prompt, "response_model": response_model, "kwargs": kwargs})
        # Check if there is a preset response for this model
        for key, resp in self.preset_responses.items():
            if response_model == type(resp):
                return resp
        # Otherwise instantiate a default model instance if possible
        try:
            return response_model()
        except Exception:
            # If default instantiation fails, construct with dummy data based on schema fields
            fields = {}
            for name, field in response_model.model_fields.items():
                if field.annotation == str:
                    fields[name] = f"mock_{name}"
                elif field.annotation == int or field.annotation == float:
                    fields[name] = 0
                elif field.annotation == bool:
                    fields[name] = False
                elif getattr(field.annotation, "__origin__", None) == list:
                    fields[name] = []
                elif getattr(field.annotation, "__origin__", None) == dict:
                    fields[name] = {}
                else:
                    fields[name] = None
            return response_model.model_validate(fields)

class OpenAIProvider(LLMProvider):
    async def generate_structured(self, prompt: str, response_model: Type[BaseModel], **kwargs: Any) -> BaseModel:
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=kwargs.get("api_key", "mock"))
            # For testing/mocking we capture connection errors
            if client.api_key == "mock-key" or client.api_key == "mock":
                raise ConnectionError("Mock connection error for OpenAI")
            # Real implementation would call client.beta.chat.completions.parse
            raise NotImplementedError("Real OpenAI provider requires live credentials")
        except ImportError:
            raise RuntimeError("openai SDK is not installed")

class AnthropicProvider(LLMProvider):
    async def generate_structured(self, prompt: str, response_model: Type[BaseModel], **kwargs: Any) -> BaseModel:
        try:
            from anthropic import AsyncAnthropic
            client = AsyncAnthropic(api_key=kwargs.get("api_key", "mock"))
            if client.api_key == "mock-key" or client.api_key == "mock":
                raise ConnectionError("Mock connection error for Anthropic")
            raise NotImplementedError("Real Anthropic provider requires live credentials")
        except ImportError:
            raise RuntimeError("anthropic SDK is not installed")

class GeminiProvider(LLMProvider):
    async def generate_structured(self, prompt: str, response_model: Type[BaseModel], **kwargs: Any) -> BaseModel:
        try:
            from google import genai
            client = genai.Client(api_key=kwargs.get("api_key", "mock"))
            if kwargs.get("api_key") in ["mock-key", "mock", None]:
                raise ConnectionError("Mock connection error for Gemini")
            raise NotImplementedError("Real Gemini provider requires live credentials")
        except ImportError:
            raise RuntimeError("google-genai SDK is not installed")

class OllamaProvider(LLMProvider):
    async def generate_structured(self, prompt: str, response_model: Type[BaseModel], **kwargs: Any) -> BaseModel:
        raise NotImplementedError("Ollama provider is not implemented yet")

class OpenRouterProvider(LLMProvider):
    async def generate_structured(self, prompt: str, response_model: Type[BaseModel], **kwargs: Any) -> BaseModel:
        raise NotImplementedError("OpenRouter provider is not implemented yet")

class FallbackLLMRouter(LLMProvider):
    def __init__(self, providers: Dict[str, LLMProvider], fallback_chain: List[str]):
        self.providers = providers
        self.fallback_chain = fallback_chain

    async def generate_structured(self, prompt: str, response_model: Type[BaseModel], **kwargs: Any) -> BaseModel:
        last_error = None
        for provider_name in self.fallback_chain:
            provider = self.providers.get(provider_name)
            if not provider:
                continue
            
            # Try running the provider with exponential backoff retries
            retries = 3
            backoff = 0.5
            for attempt in range(retries):
                try:
                    logger.info(f"Attempting LLM call using {provider_name} (Attempt {attempt+1}/{retries})")
                    return await provider.generate_structured(prompt, response_model, **kwargs)
                except (ConnectionError, TimeoutError) as e:
                    last_error = e
                    logger.warning(f"{provider_name} failed on attempt {attempt+1}: {e}")
                    if attempt < retries - 1:
                        await asyncio.sleep(backoff)
                        backoff *= 2
                except Exception as e:
                    # Non-connection errors should fail immediately or be handled
                    last_error = e
                    logger.error(f"Unrecoverable error on {provider_name}: {e}")
                    break
        
        raise RuntimeError(f"All LLM Providers in the fallback chain failed. Last error: {last_error}")
