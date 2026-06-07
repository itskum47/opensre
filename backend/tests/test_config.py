from backend.app.config.settings import Settings

def test_default_settings():
    s = Settings()
    assert s.API_ENV == "development"
    assert s.ENABLE_MEMORY is False
    assert s.ENABLE_REMEDIATION is False
    assert s.LLM_FALLBACK_CHAIN == ["anthropic", "gemini", "openai"]
