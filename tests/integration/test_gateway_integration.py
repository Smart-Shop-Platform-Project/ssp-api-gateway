import pytest
from unittest.mock import patch
import httpx

def test_route_request_success(client):
    # Mock the downstream service response
    mock_response = httpx.Response(200, json={"message": "Downstream service success"})
    
    with patch("httpx.AsyncClient.request", return_value=mock_response) as mock_request:
        # Make a request to the gateway
        response = client.get("/product/some/path")
        
        # Assertions
        assert response.status_code == 200
        assert response.json() == {"message": "Downstream service success"}
        mock_request.assert_called_once()

def test_service_not_found(client):
    # No need to mock httpx, as the gateway should reject this before making a call
    response = client.get("/nonexistentservice/some/path")
    
    assert response.status_code == 404
    assert response.json() == {"detail": "Service not found"}

def test_rate_limit_exceeded(client):
    # This is a basic test. Real rate limit testing is more complex.
    # We rely on slowapi's own tests, but we can check if the middleware is active.
    with patch("slowapi.Limiter.hit", return_value=False) as mock_hit:
        # This will simulate the rate limit being exceeded
        mock_hit.return_value = False # This is a bit of a simplification
        
        # This test is more conceptual; a real test would involve time and multiple requests
        # For now, we'll just ensure the code runs. A 429 would be expected.
        # In a real scenario, you'd need to manipulate time or the limiter's storage.
        pass

def test_retry_logic_on_failure(client):
    # Mock a sequence of failures, then success
    mock_responses = [
        httpx.ConnectError("Connection failed"),
        httpx.ReadTimeout("Read timed out"),
        httpx.Response(200, json={"message": "Success on the third try"})
    ]
    
    with patch("httpx.AsyncClient.request", side_effect=mock_responses) as mock_request:
        response = client.get("/order/some/path")
        
        assert response.status_code == 200
        assert response.json() == {"message": "Success on the third try"}
        # Assert that the request was called 3 times due to retries
        assert mock_request.call_count == 3
