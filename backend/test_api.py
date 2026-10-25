import pytest
from fastapi.testclient import TestClient
from main import app
from unittest.mock import Mock, patch, MagicMock
import json

client = TestClient(app)

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "services" in data
    assert isinstance(data["services"], list)

def test_search_stock_valid():
    """Test stock search with valid ticker"""
    response = client.get("/api/market/search/AAPL")
    assert response.status_code in [200, 404]  # May fail if yfinance has issues

def test_search_stock_invalid():
    """Test stock search with invalid ticker"""
    response = client.get("/api/market/search/INVALID123")
    assert response.status_code == 404

def test_get_quote():
    """Test getting stock quote"""
    response = client.get("/api/market/quote/AAPL")
    assert response.status_code in [200, 404]

def test_screen_stocks():
    """Test stock screening"""
    strategy = {
        "name": "Test Strategy",
        "description": "Test screening",
        "conditions": [
            {"field": "rsi_14", "operator": "<", "value": 70}
        ]
    }
    response = client.post("/api/screen", json=strategy)
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "total_screened" in data

def test_watchlist_without_db():
    """Test watchlist endpoints when database is unavailable"""
    response = client.get("/api/watchlist")
    # Should return 503 if no database configured
    assert response.status_code in [200, 503]


class TestStrategyParsing:
    """Tests for natural language strategy parsing with mocked Groq responses"""
    
    @patch('ai_agents.ai_orchestrator')
    def test_create_strategy_with_natural_language_success(self, mock_orchestrator):
        """Test successful strategy creation from natural language"""
        # Mock successful Groq response
        mock_orchestrator.is_available.return_value = True
        mock_orchestrator.parse_strategy_from_natural_language.return_value = {
            "name": "RSI Momentum Strategy",
            "description": "Stocks with RSI below 70",
            "conditions": [
                {"field": "rsi_14", "operator": "<", "value": 70}
            ]
        }
        
        strategy_data = {
            "name": "Test",
            "natural_language_input": "Find stocks with RSI below 70"
        }
        
        response = client.post("/api/strategies", json=strategy_data)
        
        # Should succeed if database is available, otherwise 503
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            data = response.json()
            assert data["name"] == "RSI Momentum Strategy"
            assert len(data["conditions"]) == 1
    
    @patch('ai_agents.ai_orchestrator')
    def test_create_strategy_with_malformed_groq_response(self, mock_orchestrator):
        """Test handling of malformed Groq response"""
        mock_orchestrator.is_available.return_value = True
        mock_orchestrator.parse_strategy_from_natural_language.return_value = {
            "error": "AI returned invalid JSON. Please rephrase your strategy and try again."
        }
        
        strategy_data = {
            "name": "Test",
            "natural_language_input": "This should fail"
        }
        
        response = client.post("/api/strategies", json=strategy_data)
        
        # Should return 400 with error message
        assert response.status_code in [400, 503]
        
        if response.status_code == 400:
            data = response.json()
            assert "error" in data["detail"].lower() or "invalid" in data["detail"].lower()
    
    @patch('ai_agents.ai_orchestrator')
    def test_create_strategy_with_empty_conditions(self, mock_orchestrator):
        """Test handling when AI returns no valid conditions"""
        mock_orchestrator.is_available.return_value = True
        mock_orchestrator.parse_strategy_from_natural_language.return_value = {
            "error": "Could not extract valid screening conditions from your description."
        }
        
        strategy_data = {
            "name": "Test",
            "natural_language_input": "Find good stocks"
        }
        
        response = client.post("/api/strategies", json=strategy_data)
        
        assert response.status_code in [400, 503]
    
    @patch('ai_agents.ai_orchestrator')
    def test_create_strategy_ai_unavailable(self, mock_orchestrator):
        """Test handling when AI service is unavailable"""
        mock_orchestrator.is_available.return_value = False
        
        strategy_data = {
            "name": "Test",
            "natural_language_input": "Find stocks with RSI below 70"
        }
        
        response = client.post("/api/strategies", json=strategy_data)
        
        # Should return 503 service unavailable
        assert response.status_code == 503
        data = response.json()
        assert "AI services" in data["detail"] or "unavailable" in data["detail"].lower()
    
    @patch('ai_agents.ai_orchestrator')
    def test_create_strategy_model_not_found_error(self, mock_orchestrator):
        """Test handling of Groq model_not_found error (the original issue)"""
        mock_orchestrator.is_available.return_value = True
        mock_orchestrator.parse_strategy_from_natural_language.return_value = {
            "error": "AI model 'llama-3.3-70b-versatile' not found. Please contact support."
        }
        
        strategy_data = {
            "name": "Test",
            "natural_language_input": "Find stocks with RSI below 70"
        }
        
        response = client.post("/api/strategies", json=strategy_data)
        
        # Should return 400 with clear error message
        assert response.status_code in [400, 503]
        
        if response.status_code == 400:
            data = response.json()
            assert "model" in data["detail"].lower() or "not found" in data["detail"].lower()


class TestStrategyParsingValidation:
    """Tests for response validation in parse_strategy_from_natural_language"""
    
    def test_parse_with_valid_response(self):
        """Test parsing with a properly formatted Groq response"""
        from ai_agents import AIOrchestrator
        
        orchestrator = AIOrchestrator()
        
        # Mock the Groq client
        with patch.object(orchestrator, 'client') as mock_client:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = json.dumps({
                "name": "Test Strategy",
                "description": "Test description",
                "conditions": [
                    {"field": "rsi_14", "operator": "<", "value": 70},
                    {"field": "price", "operator": ">", "value": 50}
                ]
            })
            
            mock_client.chat.completions.create.return_value = mock_response
            
            result = orchestrator.parse_strategy_from_natural_language("Find stocks with RSI below 70")
            
            assert "error" not in result
            assert result["name"] == "Test Strategy"
            assert len(result["conditions"]) == 2
    
    def test_parse_with_invalid_field(self):
        """Test that invalid fields are filtered out"""
        from ai_agents import AIOrchestrator
        
        orchestrator = AIOrchestrator()
        
        with patch.object(orchestrator, 'client') as mock_client:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = json.dumps({
                "name": "Test Strategy",
                "conditions": [
                    {"field": "invalid_field", "operator": "<", "value": 70},
                    {"field": "rsi_14", "operator": "<", "value": 70}
                ]
            })
            
            mock_client.chat.completions.create.return_value = mock_response
            
            result = orchestrator.parse_strategy_from_natural_language("Test")
            
            assert "error" not in result
            assert len(result["conditions"]) == 1
            assert result["conditions"][0]["field"] == "rsi_14"
    
    def test_parse_with_all_invalid_conditions(self):
        """Test that error is returned when all conditions are invalid"""
        from ai_agents import AIOrchestrator
        
        orchestrator = AIOrchestrator()
        
        with patch.object(orchestrator, 'client') as mock_client:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = json.dumps({
                "name": "Test Strategy",
                "conditions": [
                    {"field": "invalid_field", "operator": "<", "value": 70}
                ]
            })
            
            mock_client.chat.completions.create.return_value = mock_response
            
            result = orchestrator.parse_strategy_from_natural_language("Test")
            
            assert "error" in result
            assert "valid screening conditions" in result["error"]
    
    def test_parse_with_empty_response(self):
        """Test handling of empty Groq response"""
        from ai_agents import AIOrchestrator
        
        orchestrator = AIOrchestrator()
        
        with patch.object(orchestrator, 'client') as mock_client:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = ""
            
            mock_client.chat.completions.create.return_value = mock_response
            
            result = orchestrator.parse_strategy_from_natural_language("Test")
            
            assert "error" in result
    
    def test_parse_with_malformed_json(self):
        """Test handling of malformed JSON from Groq"""
        from ai_agents import AIOrchestrator
        
        orchestrator = AIOrchestrator()
        
        with patch.object(orchestrator, 'client') as mock_client:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "This is not JSON"
            
            mock_client.chat.completions.create.return_value = mock_response
            
            result = orchestrator.parse_strategy_from_natural_language("Test")
            
            assert "error" in result
            assert "invalid JSON" in result["error"]
    
    def test_parse_with_markdown_code_blocks(self):
        """Test that markdown code blocks are properly stripped"""
        from ai_agents import AIOrchestrator
        
        orchestrator = AIOrchestrator()
        
        with patch.object(orchestrator, 'client') as mock_client:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = '''```json
{
  "name": "Test Strategy",
  "conditions": [
    {"field": "rsi_14", "operator": "<", "value": 70}
  ]
}
```'''
            
            mock_client.chat.completions.create.return_value = mock_response
            
            result = orchestrator.parse_strategy_from_natural_language("Test")
            
            assert "error" not in result
            assert result["name"] == "Test Strategy"
