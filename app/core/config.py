from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "sqlite+aiosqlite:///./data/finance.db"
    SQL_ECHO: bool = False
    USE_MOCK_MARKET_DATA: bool = False
    MARKET_DATA_TIMEOUT: float = 12.0
    # Taxa livre de risco ANUAL em decimal. Ajuste para a Selic vigente
    # (ex: 0.15 = 15% a.a.). Fica em config justamente porque muda.
    RISK_FREE_RATE: float = 0.10


settings = Settings()
