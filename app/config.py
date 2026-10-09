from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    base_url: str = os.getenv("URJA_BASE_URL", "https://urja-ops.flockenergy.tech")
    username: str = os.getenv("URJA_USERNAME", "operator@urja.local")
    password: str = os.getenv("URJA_PASSWORD", "urja-ops-2026")
    timeout: float = float(os.getenv("URJA_TIMEOUT", "20"))
    user_agent: str = os.getenv(
        "URJA_USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    )


settings = Settings()
