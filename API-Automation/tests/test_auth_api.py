import os
import uuid

import pytest
from playwright.sync_api import APIRequestContext, APIResponse


LOGIN_ENDPOINT = "/login"


@pytest.fixture
def valid_credentials() -> dict[str, str]:
    email = os.getenv("FIREMEX_TEST_EMAIL")
    password = os.getenv("FIREMEX_TEST_PASSWORD")
    if not email or not password:
        pytest.fail(
            "Set FIREMEX_TEST_EMAIL and FIREMEX_TEST_PASSWORD to run "
            "the valid-credentials login tests."
        )

    return {"email": email, "password": password}


def assert_password_not_exposed(
    response: APIResponse,
    *submitted_passwords: str,
) -> None:
    response_text = response.text()
    for password in submitted_passwords:
        if password in response_text:
            pytest.fail("Response body exposed a submitted password.")

    if "application/json" not in response.headers.get("content-type", ""):
        return

    def assert_no_password_fields(value: object) -> None:
        if isinstance(value, dict):
            for key, nested_value in value.items():
                normalized_key = key.lower().replace("_", "").replace("-", "")
                assert normalized_key not in {"password", "passwordhash"}
                assert_no_password_fields(nested_value)
        elif isinstance(value, list):
            for item in value:
                assert_no_password_fields(item)

    assert_no_password_fields(response.json())


def test_login_with_valid_credentials(
    api_request_context: APIRequestContext,
    valid_credentials: dict[str, str],
) -> None:
    response = api_request_context.post(
        LOGIN_ENDPOINT,
        data=valid_credentials,
    )

    assert response.status == 200
    assert isinstance(response.json(), dict)
    assert_password_not_exposed(response, valid_credentials["password"])


def test_login_rejects_incorrect_password(
    api_request_context: APIRequestContext,
    valid_credentials: dict[str, str],
) -> None:
    incorrect_password = f"{valid_credentials['password']}-incorrect"
    response = api_request_context.post(
        LOGIN_ENDPOINT,
        data={
            "email": valid_credentials["email"],
            "password": incorrect_password,
        },
    )

    assert response.status == 401
    assert_password_not_exposed(response, incorrect_password)


def test_login_rejects_unknown_email(
    api_request_context: APIRequestContext,
) -> None:
    response = api_request_context.post(
        LOGIN_ENDPOINT,
        data={
            "email": f"unknown-{uuid.uuid4().hex}@invalid.example",
            "password": "not-a-real-password",
        },
    )

    assert response.status == 401
    assert_password_not_exposed(response, "not-a-real-password")


@pytest.mark.parametrize(
    "payload",
    [
        {"password": "not-a-real-password"},
        {"email": "missing-password@invalid.example"},
    ],
    ids=["missing-email", "missing-password"],
)
def test_login_rejects_missing_email_or_password(
    api_request_context: APIRequestContext,
    payload: dict[str, str],
) -> None:
    response = api_request_context.post(LOGIN_ENDPOINT, data=payload)

    assert response.status in {400, 422}
    assert_password_not_exposed(
        response,
        *([payload["password"]] if "password" in payload else []),
    )
