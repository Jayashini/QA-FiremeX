
def test_api_endpoint_returns_success(api_request_context):
    response = api_request_context.get("/ping")

    # Verify the HTTP response status
    assert response.status == 200

    # Verify the response is JSON
    assert "application/json" in response.headers.get(
        "content-type", ""
    )

    # Verify the response body is valid JSON
    data = response.json()

    assert isinstance(data, dict)


def test_users_endpoint_returns_json_response(api_request_context):
    response = api_request_context.get("/api/users")

    assert response.status == 200, (
        f"GET /api/users returned HTTP {response.status}: {response.text()}"
    )
    assert "application/json" in response.headers.get(
        "content-type", ""
    )

    data = response.json()
    assert isinstance(data, (list, dict))
