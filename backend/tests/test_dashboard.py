from dashboard import dashboard_component


def test_dashboard_allows_empty_access_token() -> None:
    html = dashboard_component("http://localhost:8000", "")

    assert "Missing access token" not in html
    assert "const headers = accessToken ?" in html
    assert "enable public telemetry or provide a token" in html


def test_dashboard_embeds_access_token_when_provided() -> None:
    html = dashboard_component("http://localhost:8000", "test-token")

    assert 'const accessToken = "test-token";' in html
    assert "Authorization: `Bearer ${accessToken}`" in html
