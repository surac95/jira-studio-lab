"""
Unit tests for AI service.

Tests the AIService class including classification, summarization,
combined analysis, error handling, and retry logic.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from services.ai_service import AIService
from models.ticket import Ticket
from config.settings import Settings


# Test fixtures
@pytest.fixture
def mock_settings():
    """Create a mock Settings object with required configuration."""
    settings = Mock(spec=Settings)
    settings.mistral_api_key = "test-api-key-12345"
    settings.log_level = "INFO"
    return settings


@pytest.fixture
def sample_ticket():
    """Create a sample ticket for testing."""
    return Ticket(
        key="PROJ-123",
        summary="TRIRIGA login issue",
        description="Users cannot log into TRIRIGA system",
        comments=["Affecting multiple users", "High priority issue"],
        priority="High",
        reporter="john.doe",
        created_date=datetime(2024, 1, 15, 10, 30)
    )


@pytest.fixture
def mock_mistral_client():
    """Create a mock Mistral client."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    
    # Set up the response chain
    mock_message.content = '{"category": "TRIRIGA", "confidence": 0.95, "reasoning": "Test reasoning"}'
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    mock_client.chat.complete.return_value = mock_response
    
    return mock_client


class TestAIServiceInitialization:
    """Test AIService initialization."""
    
    def test_init_success(self, mock_settings):
        """Test successful initialization with valid API key."""
        with patch('services.ai_service.MistralClient') as mock_mistral:
            service = AIService(mock_settings)
            
            assert service.settings == mock_settings
            assert service.logger is not None
            mock_mistral.assert_called_once_with(api_key="test-api-key-12345")
    
    def test_init_missing_api_key(self):
        """Test initialization fails with missing API key."""
        settings = Mock(spec=Settings)
        settings.mistral_api_key = ""
        
        with pytest.raises(ValueError, match="Mistral API key is not configured"):
            AIService(settings)
    
    def test_init_mistral_client_error(self, mock_settings):
        """Test initialization handles Mistral client creation errors."""
        with patch('services.ai_service.MistralClient', side_effect=Exception("Connection error")):
            with pytest.raises(Exception, match="Connection error"):
                AIService(mock_settings)


class TestClassifyTicket:
    """Test ticket classification functionality."""
    
    def test_classify_ticket_success(self, mock_settings, sample_ticket, mock_mistral_client):
        """Test successful ticket classification."""
        with patch('services.ai_service.MistralClient', return_value=mock_mistral_client):
            service = AIService(mock_settings)
            
            # Set up response
            mock_mistral_client.chat.complete.return_value.choices[0].message.content = \
                '{"category": "TRIRIGA", "confidence": 0.95, "reasoning": "Contains TRIRIGA keywords"}'
            
            result = service.classify_ticket(sample_ticket)
            
            assert result['category'] == "TRIRIGA"
            assert result['confidence'] == 0.95
            assert result['reasoning'] == "Contains TRIRIGA keywords"
            assert mock_mistral_client.chat.complete.called
    
    def test_classify_ticket_apic_category(self, mock_settings, mock_mistral_client):
        """Test classification of APIC ticket."""
        ticket = Ticket(
            key="PROJ-456",
            summary="API Connect gateway issue",
            description="API gateway not responding"
        )
        
        with patch('services.ai_service.MistralClient', return_value=mock_mistral_client):
            service = AIService(mock_settings)
            
            mock_mistral_client.chat.complete.return_value.choices[0].message.content = \
                '{"category": "APIC", "confidence": 0.88, "reasoning": "API Connect related"}'
            
            result = service.classify_ticket(ticket)
            
            assert result['category'] == "APIC"
            assert result['confidence'] == 0.88
    
    def test_classify_ticket_appc_category(self, mock_settings, mock_mistral_client):
        """Test classification of APPC ticket."""
        ticket = Ticket(
            key="PROJ-789",
            summary="Application error",
            description="General application issue"
        )
        
        with patch('services.ai_service.MistralClient', return_value=mock_mistral_client):
            service = AIService(mock_settings)
            
            mock_mistral_client.chat.complete.return_value.choices[0].message.content = \
                '{"category": "APPC", "confidence": 0.75, "reasoning": "General application issue"}'
            
            result = service.classify_ticket(ticket)
            
            assert result['category'] == "APPC"
            assert result['confidence'] == 0.75
    
    def test_classify_ticket_invalid_json(self, mock_settings, sample_ticket, mock_mistral_client):
        """Test classification handles invalid JSON response."""
        with patch('services.ai_service.MistralClient', return_value=mock_mistral_client):
            service = AIService(mock_settings)
            
            # Return invalid JSON
            mock_mistral_client.chat.complete.return_value.choices[0].message.content = \
                'Invalid JSON response'
            
            result = service.classify_ticket(sample_ticket)
            
            # Should return fallback classification
            assert result['category'] in ["TRIRIGA", "APIC", "APPC"]
            assert 0 <= result['confidence'] <= 1
            assert 'reasoning' in result
    
    def test_classify_ticket_invalid_category(self, mock_settings, sample_ticket, mock_mistral_client):
        """Test classification handles invalid category in response."""
        with patch('services.ai_service.MistralClient', return_value=mock_mistral_client):
            service = AIService(mock_settings)
            
            # Return invalid category
            mock_mistral_client.chat.complete.return_value.choices[0].message.content = \
                '{"category": "INVALID", "confidence": 0.9, "reasoning": "Test"}'
            
            result = service.classify_ticket(sample_ticket)
            
            # Should default to APPC
            assert result['category'] == "APPC"
            assert result['confidence'] == 0.9
    
    def test_classify_ticket_confidence_out_of_range(self, mock_settings, sample_ticket, mock_mistral_client):
        """Test classification handles confidence values outside [0, 1]."""
        with patch('services.ai_service.MistralClient', return_value=mock_mistral_client):
            service = AIService(mock_settings)
            
            # Return confidence > 1
            mock_mistral_client.chat.complete.return_value.choices[0].message.content = \
                '{"category": "TRIRIGA", "confidence": 1.5, "reasoning": "Test"}'
            
            result = service.classify_ticket(sample_ticket)
            
            # Should clamp to 1.0
            assert result['confidence'] == 1.0
    
    def test_classify_ticket_fallback_tririga(self, mock_settings, mock_mistral_client):
        """Test fallback classification for TRIRIGA keywords."""
        ticket = Ticket(
            key="PROJ-100",
            summary="TRIRIGA space management issue",
            description="Problem with facilities management in TRIRIGA"
        )
        
        with patch('services.ai_service.MistralClient', return_value=mock_mistral_client):
            service = AIService(mock_settings)
            
            # Simulate API failure
            mock_mistral_client.chat.complete.side_effect = Exception("API Error")
            
            result = service.classify_ticket(ticket)
            
            # Should use fallback with TRIRIGA keywords
            assert result['category'] == "TRIRIGA"
            assert 0 < result['confidence'] <= 0.7
            assert "Fallback" in result['reasoning']
    
    def test_classify_ticket_fallback_apic(self, mock_settings, mock_mistral_client):
        """Test fallback classification for APIC keywords."""
        ticket = Ticket(
            key="PROJ-101",
            summary="API Connect gateway problem",
            description="Issue with APIC API management"
        )
        
        with patch('services.ai_service.MistralClient', return_value=mock_mistral_client):
            service = AIService(mock_settings)
            
            # Simulate API failure
            mock_mistral_client.chat.complete.side_effect = Exception("API Error")
            
            result = service.classify_ticket(ticket)
            
            # Should use fallback with APIC keywords
            assert result['category'] == "APIC"
            assert 0 < result['confidence'] <= 0.7


class TestSummarizeTicket:
    """Test ticket summarization functionality."""
    
    def test_summarize_ticket_success(self, mock_settings, sample_ticket, mock_mistral_client):
        """Test successful ticket summarization."""
        with patch('services.ai_service.MistralClient', return_value=mock_mistral_client):
            service = AIService(mock_settings)
            
            mock_mistral_client.chat.complete.return_value.choices[0].message.content = \
                '{"summary": "Login issue affecting users", "key_points": ["Cannot login", "Multiple users", "High priority"], "urgency": "high"}'
            
            result = service.summarize_ticket(sample_ticket)
            
            assert result['summary'] == "Login issue affecting users"
            assert len(result['key_points']) == 3
            assert result['urgency'] == "high"
    
    def test_summarize_ticket_medium_urgency(self, mock_settings, mock_mistral_client):
        """Test summarization with medium urgency."""
        ticket = Ticket(
            key="PROJ-200",
            summary="Minor UI issue",
            description="Button alignment problem",
            priority="Medium"
        )
        
        with patch('services.ai_service.MistralClient', return_value=mock_mistral_client):
            service = AIService(mock_settings)
            
            mock_mistral_client.chat.complete.return_value.choices[0].message.content = \
                '{"summary": "UI alignment issue", "key_points": ["Button misaligned", "Visual issue"], "urgency": "medium"}'
            
            result = service.summarize_ticket(ticket)
            
            assert result['urgency'] == "medium"
    
    def test_summarize_ticket_low_urgency(self, mock_settings, mock_mistral_client):
        """Test summarization with low urgency."""
        ticket = Ticket(
            key="PROJ-201",
            summary="Documentation update",
            description="Update user guide",
            priority="Low"
        )
        
        with patch('services.ai_service.MistralClient', return_value=mock_mistral_client):
            service = AIService(mock_settings)
            
            mock_mistral_client.chat.complete.return_value.choices[0].message.content = \
                '{"summary": "Documentation needs update", "key_points": ["User guide", "Low priority"], "urgency": "low"}'
            
            result = service.summarize_ticket(ticket)
            
            assert result['urgency'] == "low"
    
    def test_summarize_ticket_invalid_urgency(self, mock_settings, sample_ticket, mock_mistral_client):
        """Test summarization handles invalid urgency."""
        with patch('services.ai_service.MistralClient', return_value=mock_mistral_client):
            service = AIService(mock_settings)
            
            mock_mistral_client.chat.complete.return_value.choices[0].message.content = \
                '{"summary": "Test", "key_points": ["Point 1"], "urgency": "invalid"}'
            
            result = service.summarize_ticket(sample_ticket)
            
            # Should default to medium
            assert result['urgency'] == "medium"
    
    def test_summarize_ticket_key_points_not_list(self, mock_settings, sample_ticket, mock_mistral_client):
        """Test summarization handles non-list key_points."""
        with patch('services.ai_service.MistralClient', return_value=mock_mistral_client):
            service = AIService(mock_settings)
            
            mock_mistral_client.chat.complete.return_value.choices[0].message.content = \
                '{"summary": "Test", "key_points": "Single point", "urgency": "low"}'
            
            result = service.summarize_ticket(sample_ticket)
            
            # Should convert to list
            assert isinstance(result['key_points'], list)
            assert len(result['key_points']) == 1
    
    def test_summarize_ticket_fallback(self, mock_settings, sample_ticket, mock_mistral_client):
        """Test fallback summarization when API fails."""
        with patch('services.ai_service.MistralClient', return_value=mock_mistral_client):
            service = AIService(mock_settings)
            
            # Simulate API failure
            mock_mistral_client.chat.complete.side_effect = Exception("API Error")
            
            result = service.summarize_ticket(sample_ticket)
            
            # Should return fallback summary
            assert sample_ticket.key in result['summary']
            assert isinstance(result['key_points'], list)
            assert result['urgency'] in ["low", "medium", "high"]
    
    def test_summarize_ticket_fallback_urgency_mapping(self, mock_settings, mock_mistral_client):
        """Test fallback urgency mapping from priority."""
        # Test high priority -> medium urgency
        ticket_high = Ticket(key="T-1", summary="Test", priority="High")
        
        with patch('services.ai_service.MistralClient', return_value=mock_mistral_client):
            service = AIService(mock_settings)
            mock_mistral_client.chat.complete.side_effect = Exception("API Error")
            
            result = service.summarize_ticket(ticket_high)
            assert result['urgency'] == "medium"
        
        # Test critical priority -> high urgency
        ticket_critical = Ticket(key="T-2", summary="Test", priority="Critical")
        
        with patch('services.ai_service.MistralClient', return_value=mock_mistral_client):
            service = AIService(mock_settings)
            mock_mistral_client.chat.complete.side_effect = Exception("API Error")
            
            result = service.summarize_ticket(ticket_critical)
            assert result['urgency'] == "high"


class TestAnalyzeTicket:
    """Test combined ticket analysis functionality."""
    
    def test_analyze_ticket_success(self, mock_settings, sample_ticket, mock_mistral_client):
        """Test successful combined analysis."""
        with patch('services.ai_service.MistralClient', return_value=mock_mistral_client):
            service = AIService(mock_settings)
            
            mock_mistral_client.chat.complete.return_value.choices[0].message.content = \
                '{"category": "TRIRIGA", "confidence": 0.92, "reasoning": "TRIRIGA issue", "summary": "Login problem", "key_points": ["Cannot login", "Multiple users"], "urgency": "high"}'
            
            result = service.analyze_ticket(sample_ticket)
            
            # Check classification fields
            assert result['category'] == "TRIRIGA"
            assert result['confidence'] == 0.92
            assert result['reasoning'] == "TRIRIGA issue"
            
            # Check summarization fields
            assert result['summary'] == "Login problem"
            assert len(result['key_points']) == 2
            assert result['urgency'] == "high"
    
    def test_analyze_ticket_missing_fields(self, mock_settings, sample_ticket, mock_mistral_client):
        """Test analysis handles missing fields in response."""
        with patch('services.ai_service.MistralClient', return_value=mock_mistral_client):
            service = AIService(mock_settings)
            
            # Missing summary field
            mock_mistral_client.chat.complete.return_value.choices[0].message.content = \
                '{"category": "TRIRIGA", "confidence": 0.9, "reasoning": "Test"}'
            
            result = service.analyze_ticket(sample_ticket)
            
            # Should return fallback
            assert 'category' in result
            assert 'summary' in result
            assert 'urgency' in result
    
    def test_analyze_ticket_fallback(self, mock_settings, sample_ticket, mock_mistral_client):
        """Test fallback analysis when API fails."""
        with patch('services.ai_service.MistralClient', return_value=mock_mistral_client):
            service = AIService(mock_settings)
            
            # Simulate API failure
            mock_mistral_client.chat.complete.side_effect = Exception("API Error")
            
            result = service.analyze_ticket(sample_ticket)
            
            # Should return combined fallback
            assert 'category' in result
            assert 'confidence' in result
            assert 'reasoning' in result
            assert 'summary' in result
            assert 'key_points' in result
            assert 'urgency' in result


class TestRetryLogic:
    """Test retry logic for API calls."""
    
    def test_retry_success_on_second_attempt(self, mock_settings, sample_ticket, mock_mistral_client):
        """Test successful retry after initial failure."""
        with patch('services.ai_service.MistralClient', return_value=mock_mistral_client):
            service = AIService(mock_settings)
            
            # Fail first, succeed second
            mock_mistral_client.chat.complete.side_effect = [
                Exception("Temporary error"),
                mock_mistral_client.chat.complete.return_value
            ]
            
            # Reset side_effect for the successful call
            success_response = MagicMock()
            success_choice = MagicMock()
            success_message = MagicMock()
            success_message.content = '{"category": "TRIRIGA", "confidence": 0.9, "reasoning": "Test"}'
            success_choice.message = success_message
            success_response.choices = [success_choice]
            
            mock_mistral_client.chat.complete.side_effect = [
                Exception("Temporary error"),
                success_response
            ]
            
            result = service.classify_ticket(sample_ticket)
            
            # Should succeed after retry
            assert result['category'] == "TRIRIGA"
            assert mock_mistral_client.chat.complete.call_count == 2
    
    def test_retry_exhausted(self, mock_settings, sample_ticket, mock_mistral_client):
        """Test all retries exhausted."""
        with patch('services.ai_service.MistralClient', return_value=mock_mistral_client):
            service = AIService(mock_settings)
            
            # Always fail
            mock_mistral_client.chat.complete.side_effect = Exception("Persistent error")
            
            result = service.classify_ticket(sample_ticket)
            
            # Should return fallback after all retries
            assert 'category' in result
            assert mock_mistral_client.chat.complete.call_count == service.MAX_RETRIES
    
    def test_retry_with_exponential_backoff(self, mock_settings, sample_ticket, mock_mistral_client):
        """Test retry uses exponential backoff."""
        with patch('services.ai_service.MistralClient', return_value=mock_mistral_client):
            with patch('services.ai_service.time.sleep') as mock_sleep:
                service = AIService(mock_settings)
                
                # Always fail
                mock_mistral_client.chat.complete.side_effect = Exception("Error")
                
                service.classify_ticket(sample_ticket)
                
                # Check sleep was called with increasing delays
                assert mock_sleep.call_count == service.MAX_RETRIES - 1
                # First delay: 1 second, second delay: 2 seconds
                calls = [call[0][0] for call in mock_sleep.call_args_list]
                assert calls[0] == 1
                assert calls[1] == 2


class TestErrorHandling:
    """Test error handling scenarios."""
    
    def test_empty_response_from_mistral(self, mock_settings, sample_ticket, mock_mistral_client):
        """Test handling of empty response from Mistral."""
        with patch('services.ai_service.MistralClient', return_value=mock_mistral_client):
            service = AIService(mock_settings)
            
            # Return empty choices
            mock_mistral_client.chat.complete.return_value.choices = []
            
            result = service.classify_ticket(sample_ticket)
            
            # Should return fallback
            assert 'category' in result
            assert 'confidence' in result
    
    def test_network_error(self, mock_settings, sample_ticket, mock_mistral_client):
        """Test handling of network errors."""
        with patch('services.ai_service.MistralClient', return_value=mock_mistral_client):
            service = AIService(mock_settings)
            
            mock_mistral_client.chat.complete.side_effect = ConnectionError("Network error")
            
            result = service.classify_ticket(sample_ticket)
            
            # Should return fallback
            assert 'category' in result
    
    def test_rate_limit_error(self, mock_settings, sample_ticket, mock_mistral_client):
        """Test handling of rate limit errors."""
        with patch('services.ai_service.MistralClient', return_value=mock_mistral_client):
            service = AIService(mock_settings)
            
            mock_mistral_client.chat.complete.side_effect = Exception("Rate limit exceeded")
            
            result = service.classify_ticket(sample_ticket)
            
            # Should return fallback after retries
            assert 'category' in result


class TestPromptBuilding:
    """Test prompt building methods."""
    
    def test_classification_prompt_includes_ticket_info(self, mock_settings, sample_ticket):
        """Test classification prompt includes all ticket information."""
        with patch('services.ai_service.MistralClient'):
            service = AIService(mock_settings)
            
            prompt = service._build_classification_prompt(sample_ticket)
            
            assert sample_ticket.key in prompt
            assert sample_ticket.summary in prompt
            assert sample_ticket.description in prompt
            assert sample_ticket.priority in prompt
            assert "TRIRIGA" in prompt
            assert "APIC" in prompt
            assert "APPC" in prompt
    
    def test_summarization_prompt_includes_ticket_info(self, mock_settings, sample_ticket):
        """Test summarization prompt includes all ticket information."""
        with patch('services.ai_service.MistralClient'):
            service = AIService(mock_settings)
            
            prompt = service._build_summarization_prompt(sample_ticket)
            
            assert sample_ticket.key in prompt
            assert sample_ticket.summary in prompt
            assert sample_ticket.description in prompt
            assert sample_ticket.priority in prompt
    
    def test_combined_prompt_includes_all_requirements(self, mock_settings, sample_ticket):
        """Test combined prompt includes classification and summarization requirements."""
        with patch('services.ai_service.MistralClient'):
            service = AIService(mock_settings)
            
            prompt = service._build_combined_prompt(sample_ticket)
            
            # Check ticket info
            assert sample_ticket.key in prompt
            assert sample_ticket.summary in prompt
            
            # Check classification requirements
            assert "TRIRIGA" in prompt
            assert "APIC" in prompt
            assert "APPC" in prompt
            
            # Check summarization requirements
            assert "summary" in prompt.lower()
            assert "key_points" in prompt.lower()
            assert "urgency" in prompt.lower()


# Made with Bob