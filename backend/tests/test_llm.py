import pytest
from pydantic import BaseModel
from backend.app.providers.llm import MockLLMProvider, FallbackLLMRouter, LLMProvider

class DummyModel(BaseModel):
    name: str
    value: int

@pytest.mark.asyncio
async def test_mock_llm_provider():
    m = MockLLMProvider()
    res = await m.generate_structured("Hello", DummyModel)
    assert isinstance(res, DummyModel)
    assert res.name == "mock_name"
    assert res.value == 0

@pytest.mark.asyncio
async def test_fallback_llm_router():
    class FailingProvider(LLMProvider):
        async def generate_structured(self, prompt, response_model, **kwargs):
            raise ConnectionError("Connection failed")

    class WorkingProvider(LLMProvider):
        async def generate_structured(self, prompt, response_model, **kwargs):
            return response_model(name="working", value=100)

    providers = {
        "failing": FailingProvider(),
        "working": WorkingProvider()
    }
    
    router = FallbackLLMRouter(providers=providers, fallback_chain=["failing", "working"])
    res = await router.generate_structured("Hello", DummyModel)
    assert res.name == "working"
    assert res.value == 100
