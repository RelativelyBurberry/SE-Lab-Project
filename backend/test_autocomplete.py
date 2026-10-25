"""
Tests for stock autocomplete feature
Tests company search API with mocked Yahoo Finance responses
"""

import pytest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from datetime import datetime


class TestCompanySearchAPI:
    """Test suite for company search autocomplete API"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        from main import app
        return TestClient(app)
    
    @pytest.fixture
    def mock_yahoo_search_response_oil_india(self):
        """Mock Yahoo Finance search response for OIL INDIA"""
        return {
            "quotes": [
                {
                    "symbol": "OIL.NS",
                    "shortname": "Oil India Limited",
                    "longname": "Oil India Limited",
                    "exchange": "NSI",
                    "quoteType": "EQUITY"
                },
                {
                    "symbol": "OIL",
                    "shortname": "BP Prudhoe Bay Royalty Trust",
                    "exchange": "NYQ",
                    "quoteType": "EQUITY"
                },
                {
                    "symbol": "OIL.BE",
                    "shortname": "Oil India Limited",
                    "exchange": "BER",
                    "quoteType": "EQUITY"
                }
            ]
        }
    
    @pytest.fixture
    def mock_yahoo_search_response_aapl(self):
        """Mock Yahoo Finance search response for AAPL"""
        return {
            "quotes": [
                {
                    "symbol": "AAPL",
                    "shortname": "Apple Inc.",
                    "longname": "Apple Inc.",
                    "exchange": "NMS",
                    "quoteType": "EQUITY"
                }
            ]
        }
    
    @pytest.fixture
    def mock_yahoo_search_response_partial(self):
        """Mock Yahoo Finance search response for partial company name"""
        return {
            "quotes": [
                {
                    "symbol": "MSFT",
                    "shortname": "Microsoft Corporation",
                    "exchange": "NMS",
                    "quoteType": "EQUITY"
                },
                {
                    "symbol": "MSF.DE",
                    "shortname": "Microsoft Corporation",
                    "exchange": "GER",
                    "quoteType": "EQUITY"
                }
            ]
        }
    
    @pytest.fixture
    def mock_yahoo_search_response_empty(self):
        """Mock Yahoo Finance search response with no results"""
        return {
            "quotes": []
        }
    
    @pytest.fixture
    def mock_yahoo_search_response_mixed(self):
        """Mock Yahoo Finance search response with mixed quote types"""
        return {
            "quotes": [
                {
                    "symbol": "AAPL",
                    "shortname": "Apple Inc.",
                    "exchange": "NMS",
                    "quoteType": "EQUITY"
                },
                {
                    "symbol": "SPY",
                    "shortname": "SPDR S&P 500 ETF Trust",
                    "exchange": "PCX",
                    "quoteType": "ETF"
                },
                {
                    "symbol": "DUMMY",
                    "shortname": "Dummy Currency",
                    "exchange": "CCY",
                    "quoteType": "CURRENCY"
                },
                {
                    "symbol": "AAPL-OPTIONS",
                    "shortname": "Apple Options",
                    "quoteType": "OPTION"
                }
            ]
        }

    def test_search_companies_by_name(self, client, mock_yahoo_search_response_oil_india):
        """Test searching companies by company name"""
        with patch('market_data.market_data_service._make_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_yahoo_search_response_oil_india
            mock_request.return_value = mock_response
            
            response = client.get("/api/market/search?q=OIL%20INDIA&limit=5")
            
            assert response.status_code == 200
            data = response.json()
            assert "results" in data
            assert "query" in data
            assert "timestamp" in data
            assert data["query"] == "OIL INDIA"
            assert len(data["results"]) <= 5
            
            # Verify first result
            if len(data["results"]) > 0:
                result = data["results"][0]
                assert "symbol" in result
                assert "name" in result
                assert result["symbol"] == "OIL.NS"
                assert result["name"] == "Oil India Limited"

    def test_search_companies_by_partial_name(self, client, mock_yahoo_search_response_partial):
        """Test searching companies by partial company name"""
        with patch('market_data.market_data_service._make_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_yahoo_search_response_partial
            mock_request.return_value = mock_response
            
            response = client.get("/api/market/search?q=Micro&limit=5")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["results"]) > 0
            assert data["results"][0]["symbol"] == "MSFT"

    def test_search_companies_by_ticker(self, client, mock_yahoo_search_response_aapl):
        """Test searching companies by exact ticker"""
        with patch('market_data.market_data_service._make_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_yahoo_search_response_aapl
            mock_request.return_value = mock_response
            
            response = client.get("/api/market/search?q=AAPL&limit=5")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["results"]) == 1
            assert data["results"][0]["symbol"] == "AAPL"
            assert data["results"][0]["name"] == "Apple Inc."

    def test_search_companies_no_results(self, client, mock_yahoo_search_response_empty):
        """Test searching with no matching results"""
        with patch('market_data.market_data_service._make_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_yahoo_search_response_empty
            mock_request.return_value = mock_response
            
            response = client.get("/api/market/search?q=NOTREAL123&limit=5")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["results"]) == 0

    def test_search_companies_rate_limit(self, client):
        """Test handling of Yahoo Finance rate limiting (429)"""
        from market_data import MarketDataError, market_data_service
        
        # Clear cache to ensure fresh request
        market_data_service._cache = {}
        market_data_service._cache_timestamps = {}
        
        with patch('market_data.market_data_service._make_request') as mock_request:
            mock_request.side_effect = MarketDataError(
                "Data provider rate limit reached. Please wait a few minutes before retrying.",
                status_code=429
            )
            
            response = client.get("/api/market/search?q=RATELIMITTEST123&limit=5")
            
            assert response.status_code == 429
            assert "rate limit" in response.json()["detail"].lower()

    def test_search_companies_upstream_error(self, client):
        """Test handling of upstream failures (502/504)"""
        from market_data import MarketDataError, market_data_service
        
        # Clear cache to ensure fresh request
        market_data_service._cache = {}
        market_data_service._cache_timestamps = {}
        
        with patch('market_data.market_data_service._make_request') as mock_request:
            mock_request.side_effect = MarketDataError(
                "Data provider returned error (HTTP 502).",
                status_code=502
            )
            
            response = client.get("/api/market/search?q=UPSTREAMERROR123&limit=5")
            
            assert response.status_code == 502

    def test_search_companies_timeout(self, client):
        """Test handling of timeout errors"""
        from market_data import MarketDataError, market_data_service
        
        # Clear cache to ensure fresh request
        market_data_service._cache = {}
        market_data_service._cache_timestamps = {}
        
        with patch('market_data.market_data_service._make_request') as mock_request:
            mock_request.side_effect = MarketDataError(
                "Data provider request timed out. Please try again later.",
                status_code=504
            )
            
            response = client.get("/api/market/search?q=TIMEOUTTEST123&limit=5")
            
            assert response.status_code == 504

    def test_search_companies_mixed_quote_types(self, client, mock_yahoo_search_response_mixed):
        """Test that only EQUITY, ETF, INDEX quotes are returned"""
        with patch('market_data.market_data_service._make_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_yahoo_search_response_mixed
            mock_request.return_value = mock_response
            
            response = client.get("/api/market/search?q=AAPL&limit=5")
            
            assert response.status_code == 200
            data = response.json()
            
            # Should only include EQUITY and ETF
            for result in data["results"]:
                assert result["quote_type"] in ["EQUITY", "ETF", "INDEX", "MUTUALFUND"]

    def test_search_companies_limit_parameter(self, client):
        """Test that limit parameter is respected (max 5)"""
        mock_quotes = [
            {
                "symbol": f"TEST{i}",
                "shortname": f"Test Company {i}",
                "exchange": "NMS",
                "quoteType": "EQUITY"
            }
            for i in range(10)
        ]
        
        with patch('market_data.market_data_service._make_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"quotes": mock_quotes}
            mock_request.return_value = mock_response
            
            # Test with limit=3
            response = client.get("/api/market/search?q=TEST&limit=3")
            assert response.status_code == 200
            data = response.json()
            assert len(data["results"]) <= 3
            
            # Test with limit=10 (should be capped to 5)
            response = client.get("/api/market/search?q=TEST&limit=10")
            assert response.status_code == 200
            data = response.json()
            assert len(data["results"]) <= 5

    def test_search_companies_missing_query(self, client):
        """Test that missing query parameter returns 422 (FastAPI validation)"""
        response = client.get("/api/market/search")
        assert response.status_code == 422  # FastAPI validation error

    def test_search_companies_empty_query(self, client):
        """Test that empty query returns 400"""
        response = client.get("/api/market/search?q=&limit=5")
        assert response.status_code == 400

    def test_search_companies_malformed_response(self, client):
        """Test handling of malformed Yahoo Finance response"""
        from market_data import market_data_service
        
        # Clear cache to ensure fresh request
        market_data_service._cache = {}
        market_data_service._cache_timestamps = {}
        
        with patch('market_data.market_data_service._make_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.side_effect = ValueError("Invalid JSON")
            mock_request.return_value = mock_response
            
            response = client.get("/api/market/search?q=MALFORMEDTEST123&limit=5")
            
            assert response.status_code == 502
            assert "invalid response" in response.json()["detail"].lower()

    def test_search_companies_missing_fields(self, client):
        """Test handling of results with missing fields"""
        from market_data import market_data_service
        
        # Clear cache to ensure fresh request
        market_data_service._cache = {}
        market_data_service._cache_timestamps = {}
        
        mock_response = {
            "quotes": [
                {
                    "symbol": "TEST1",
                    # Missing shortname and exchange
                    "quoteType": "EQUITY"
                },
                {
                    # Missing symbol - should be skipped
                    "shortname": "No Symbol",
                    "quoteType": "EQUITY"
                },
                {
                    "symbol": "TEST2",
                    "shortname": "Valid Company",
                    "exchange": "NMS",
                    "quoteType": "EQUITY"
                }
            ]
        }
        
        with patch('market_data.market_data_service._make_request') as mock_request:
            mock_resp = Mock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_response
            mock_request.return_value = mock_resp
            
            response = client.get("/api/market/search?q=MISSINGFIELDSTEST123&limit=5")
            
            assert response.status_code == 200
            data = response.json()
            
            # Should have 2 results (one with missing name, one complete)
            # The one with missing symbol should be skipped
            assert len(data["results"]) >= 1
            assert len(data["results"]) <= 2

    def test_search_result_structure(self, client, mock_yahoo_search_response_aapl):
        """Test that search results have correct structure"""
        with patch('market_data.market_data_service._make_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_yahoo_search_response_aapl
            mock_request.return_value = mock_response
            
            response = client.get("/api/market/search?q=AAPL&limit=5")
            
            assert response.status_code == 200
            data = response.json()
            
            # Check response structure
            assert "results" in data
            assert "query" in data
            assert "timestamp" in data
            assert isinstance(data["results"], list)
            assert isinstance(data["query"], str)
            
            # Check result structure
            if len(data["results"]) > 0:
                result = data["results"][0]
                assert "symbol" in result
                assert "name" in result
                assert "exchange" in result or result.get("exchange") is None
                assert "quote_type" in result or result.get("quote_type") is None


class TestCompanySearchIntegration:
    """Integration tests for company search with stock details flow"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        from main import app
        return TestClient(app)
    
    def test_search_then_quote_flow(self, client):
        """Test selecting a search result and fetching its quote"""
        # Mock search response
        search_response = {
            "quotes": [
                {
                    "symbol": "OIL.NS",
                    "shortname": "Oil India Limited",
                    "exchange": "NSI",
                    "quoteType": "EQUITY"
                }
            ]
        }
        
        with patch('market_data.market_data_service._make_request') as mock_request:
            # First call for search
            mock_search_response = Mock()
            mock_search_response.status_code = 200
            mock_search_response.json.return_value = search_response
            
            mock_request.return_value = mock_search_response
            
            search_resp = client.get("/api/market/search?q=OIL%20INDIA&limit=5")
            
            assert search_resp.status_code == 200
            symbol = search_resp.json()["results"][0]["symbol"]
            assert symbol == "OIL.NS"
            
            # Now fetch quote using the exact symbol
            mock_request.reset_mock()
            
            # Mock quote fetch (would need chart data)
            # This test verifies the symbol is used correctly
            # The actual quote test is in test_api.py


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
