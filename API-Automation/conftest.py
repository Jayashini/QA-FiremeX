
import os
from pathlib import Path

import pytest
from playwright.sync_api import Playwright, APIRequestContext


def load_local_env() -> None:
    env_file = Path(__file__).with_name(".env")
    if not env_file.exists():
        return

    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        name, separator, value = line.partition("=")
        if not separator:
            raise ValueError(f"Invalid environment entry in {env_file}")

        name = name.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ.setdefault(name, value)


load_local_env()


@pytest.fixture(scope="session")
def api_request_context(
    playwright: Playwright,
) -> APIRequestContext:
    base_url = os.getenv(
        "FIREMEX_API_URL",
        os.getenv("API_BASE_URL", "http://localhost:8080"),
    )
    api_token = os.getenv("FIREMEX_API_TOKEN") or os.getenv("API_TOKEN")
    headers = {"Accept": "application/json"}
    if api_token:
        headers["Authorization"] = f"Bearer {api_token}"

    context = playwright.request.new_context(
        base_url=base_url,
        extra_http_headers=headers,
        timeout=10000,
    )

    yield context
    context.dispose()
