from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    # API Configurations
    API_ENV: str = "development"
    DATABASE_URL: str = "sqlite:///./opensre.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    # LLM Provider Keys
    OPENAI_API_KEY: str = "mock-key"
    ANTHROPIC_API_KEY: str = "mock-key"
    GEMINI_API_KEY: str = "mock-key"
    OLLAMA_HOST: str = "http://localhost:11434"
    OPENROUTER_API_KEY: str = "mock-key"

    # Integration Endpoints & Credentials
    PROMETHEUS_URL: str = "http://localhost:9090"
    LOKI_URL: str = "http://localhost:3100"
    GITHUB_TOKEN: str = "mock-token"
    GITHUB_REPO: str = "owner/repo"

    # Neo4j Configurations
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"

    # Slack Configurations
    SLACK_BOT_TOKEN: str = "mock-token"
    SLACK_CHANNEL: str = "general"
    SLACK_SIGNING_SECRET: str = "mock-secret"

    # PagerDuty Configurations
    PAGERDUTY_API_KEY: str = "mock-key"
    PAGERDUTY_ROUTING_KEY: str = "mock-key"

    # Feature Flags
    ENABLE_MEMORY: bool = False
    ENABLE_REMEDIATION: bool = False
    ENABLE_MCP: bool = False
    ENABLE_SLACK: bool = False
    ENABLE_PAGERDUTY: bool = False

    # Fallback Chain Order
    LLM_FALLBACK_CHAIN: List[str] = ["anthropic", "gemini", "openai"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

