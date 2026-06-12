"""
AI service for ticket classification and summarization using Mistral AI.

This module provides AI-powered analysis of JIRA tickets including:
- Classification into categories (TRIRIGA, APIC, APPC)
- Summarization for Slack notifications
- Combined analysis operations
"""

import json
import time
from typing import Dict, Any, List, Optional
from mistralai.client import MistralClient

from config.settings import Settings
from models.ticket import Ticket
from utils.logger import get_logger


class AIService:
    """
    Service for AI-powered ticket analysis using Mistral AI.
    
    This service provides methods for classifying tickets into categories
    and generating concise summaries for team notifications.
    
    Attributes:
        settings: Application settings instance
        client: Mistral AI client instance
        logger: Logger instance for this service
    """
    
    # Classification categories
    CATEGORIES = ["TRIRIGA", "APIC", "APPC"]
    
    # Urgency levels
    URGENCY_LEVELS = ["low", "medium", "high"]
    
    # Model configuration
    CLASSIFICATION_MODEL = "mistral-large-latest"
    SUMMARIZATION_MODEL = "mistral-large-latest"
    CLASSIFICATION_TEMPERATURE = 0.3
    SUMMARIZATION_TEMPERATURE = 0.5
    
    # Retry configuration
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # seconds
    RETRY_BACKOFF = 2  # exponential backoff multiplier
    
    def __init__(self, settings: Settings):
        """
        Initialize the AI service with Mistral AI client.
        
        Args:
            settings: Settings instance containing API keys and configuration
            
        Raises:
            ValueError: If Mistral API key is not configured
        """
        self.settings = settings
        self.logger = get_logger(__name__)
        
        # Validate API key
        if not settings.mistral_api_key:
            raise ValueError("Mistral API key is not configured")
        
        # Initialize Mistral client
        try:
            self.client = MistralClient(api_key=settings.mistral_api_key)
            self.logger.info("Mistral AI client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Mistral AI client: {e}")
            raise
    
    def classify_ticket(self, ticket: Ticket) -> Dict[str, Any]:
        """
        Classify a ticket into one of the predefined categories.
        
        Uses Mistral AI to analyze the ticket content and determine which
        category it belongs to: TRIRIGA, APIC, or APPC.
        
        Args:
            ticket: Ticket instance to classify
            
        Returns:
            Dictionary containing:
                - category (str): Classification category
                - confidence (float): Confidence score (0-1)
                - reasoning (str): Explanation for the classification
                
        Example:
            >>> ai_service = AIService(settings)
            >>> ticket = Ticket(key="PROJ-123", summary="TRIRIGA login issue")
            >>> result = ai_service.classify_ticket(ticket)
            >>> print(result['category'])  # "TRIRIGA"
            >>> print(result['confidence'])  # 0.95
        """
        self.logger.info(f"Classifying ticket: {ticket.key}")
        
        # Build classification prompt
        prompt = self._build_classification_prompt(ticket)
        
        try:
            # Call Mistral AI with retry logic
            response = self._call_mistral_with_retry(
                prompt=prompt,
                model=self.CLASSIFICATION_MODEL,
                temperature=self.CLASSIFICATION_TEMPERATURE
            )
            
            # Parse and validate response
            result = self._parse_classification_response(response)
            
            self.logger.info(
                f"Ticket {ticket.key} classified as {result['category']} "
                f"with confidence {result['confidence']:.2f}"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Classification failed for {ticket.key}: {e}")
            # Return fallback classification
            return self._fallback_classification(ticket)
    
    def summarize_ticket(self, ticket: Ticket) -> Dict[str, Any]:
        """
        Generate a concise summary of a ticket for Slack notifications.
        
        Uses Mistral AI to create a brief summary, extract key points,
        and assess the urgency of the ticket.
        
        Args:
            ticket: Ticket instance to summarize
            
        Returns:
            Dictionary containing:
                - summary (str): 2-3 sentence summary
                - key_points (List[str]): 3-5 key points
                - urgency (str): Urgency level (low/medium/high)
                
        Example:
            >>> ai_service = AIService(settings)
            >>> ticket = Ticket(key="PROJ-123", summary="Critical API issue")
            >>> result = ai_service.summarize_ticket(ticket)
            >>> print(result['summary'])
            >>> print(result['urgency'])  # "high"
        """
        self.logger.info(f"Summarizing ticket: {ticket.key}")
        
        # Build summarization prompt
        prompt = self._build_summarization_prompt(ticket)
        
        try:
            # Call Mistral AI with retry logic
            response = self._call_mistral_with_retry(
                prompt=prompt,
                model=self.SUMMARIZATION_MODEL,
                temperature=self.SUMMARIZATION_TEMPERATURE
            )
            
            # Parse and validate response
            result = self._parse_summarization_response(response)
            
            self.logger.info(
                f"Ticket {ticket.key} summarized with urgency: {result['urgency']}"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Summarization failed for {ticket.key}: {e}")
            # Return fallback summary
            return self._fallback_summarization(ticket)
    
    def analyze_ticket(self, ticket: Ticket) -> Dict[str, Any]:
        """
        Perform both classification and summarization in a single operation.
        
        This is more efficient than calling classify_ticket() and
        summarize_ticket() separately, as it makes a single API call.
        
        Args:
            ticket: Ticket instance to analyze
            
        Returns:
            Dictionary containing both classification and summary results:
                - category (str): Classification category
                - confidence (float): Classification confidence (0-1)
                - reasoning (str): Classification reasoning
                - summary (str): Ticket summary
                - key_points (List[str]): Key points
                - urgency (str): Urgency level
                
        Example:
            >>> ai_service = AIService(settings)
            >>> ticket = Ticket(key="PROJ-123", summary="TRIRIGA issue")
            >>> result = ai_service.analyze_ticket(ticket)
            >>> print(f"{result['category']}: {result['summary']}")
        """
        self.logger.info(f"Analyzing ticket: {ticket.key}")
        
        # Build combined analysis prompt
        prompt = self._build_combined_prompt(ticket)
        
        try:
            # Call Mistral AI with retry logic
            response = self._call_mistral_with_retry(
                prompt=prompt,
                model=self.CLASSIFICATION_MODEL,
                temperature=self.CLASSIFICATION_TEMPERATURE
            )
            
            # Parse and validate response
            result = self._parse_combined_response(response)
            
            self.logger.info(
                f"Ticket {ticket.key} analyzed: {result['category']} "
                f"(confidence: {result['confidence']:.2f}), "
                f"urgency: {result['urgency']}"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Analysis failed for {ticket.key}: {e}")
            # Return fallback analysis
            classification = self._fallback_classification(ticket)
            summary = self._fallback_summarization(ticket)
            
            # Combine fallback results
            result = {**classification, **summary}
            
            self.logger.info(
                f"Ticket {ticket.key} analyzed (fallback): {result['category']} "
                f"(confidence: {result['confidence']:.2f}), "
                f"urgency: {result['urgency']}"
            )
            
            return result
    
    def analyze_ticket_deep(self, ticket: Ticket) -> Dict[str, Any]:
        """
        Perform deep technical analysis of a ticket.
        
        This method provides comprehensive analysis including root cause,
        solutions, impact assessment, and diagnostic steps. It's designed
        to be called on-demand when users request detailed analysis.
        
        Args:
            ticket: Ticket instance to analyze deeply
            
        Returns:
            Dictionary containing deep analysis:
                - root_cause (str): Root cause analysis
                - solutions (List[str]): Recommended solutions (prioritized)
                - impact (str): Impact assessment
                - next_steps (List[str]): Diagnostic/action steps
                - estimated_resolution_time (str): Time estimate
                - confidence (float): Analysis confidence (0-1)
                
        Example:
            >>> ai_service = AIService(settings)
            >>> ticket = Ticket(key="PROJ-123", summary="TRIRIGA issue")
            >>> deep = ai_service.analyze_ticket_deep(ticket)
            >>> print(deep['root_cause'])
        """
        self.logger.info(f"Performing deep analysis for ticket: {ticket.key}")
        
        # Build deep analysis prompt
        prompt = self._build_deep_analysis_prompt(ticket)
        
        try:
            # Call Mistral AI with retry logic
            response = self._call_mistral_with_retry(
                prompt=prompt,
                model=self.CLASSIFICATION_MODEL,
                temperature=0.4  # Slightly higher for more creative solutions
            )
            
            # Parse and validate response
            result = self._parse_deep_analysis_response(response)
            
            self.logger.info(
                f"Deep analysis completed for {ticket.key}: "
                f"{len(result.get('solutions', []))} solutions identified"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Deep analysis failed for {ticket.key}: {e}")
            # Return fallback deep analysis
            return self._fallback_deep_analysis(ticket)
    
    def _build_deep_analysis_prompt(self, ticket: Ticket) -> str:
        """Build the deep analysis prompt for Mistral AI."""
        return f"""You are a senior technical support engineer with expertise in IBM TRIRIGA, API Connect, and enterprise applications. 
Perform a comprehensive technical analysis of this support ticket.

Ticket Information:
Key: {ticket.key}
Summary: {ticket.summary}
Description: {ticket.description}
Priority: {ticket.priority}
Reporter: {ticket.reporter}
Created: {ticket.created_date}

Comments ({len(ticket.comments)} total):
{chr(10).join([f"- {comment[:200]}..." if len(comment) > 200 else f"- {comment}" for comment in ticket.comments[:5]])}

Attachments: {', '.join(ticket.attachments) if ticket.attachments else 'None'}

Provide a detailed technical analysis including:

1. **Root Cause Analysis**: Identify the underlying technical issue causing this problem. Consider:
   - System architecture and integration points
   - Authentication/session management
   - Configuration issues
   - Known patterns and common issues

2. **Recommended Solutions**: Provide 3-5 prioritized solutions:
   - Quick fixes (immediate workarounds)
   - Proper fixes (addressing root cause)
   - Long-term improvements (preventing recurrence)

3. **Impact Assessment**: Evaluate:
   - Current impact (users affected, business operations)
   - Potential escalation risks
   - Urgency for resolution

4. **Next Steps**: Provide specific diagnostic or action steps:
   - What logs to check
   - What configurations to review
   - What tests to perform
   - Who to involve (if cross-team)

5. **Estimated Resolution Time**: Provide realistic time estimate based on complexity

Respond in JSON format:
{{
    "root_cause": "detailed root cause analysis",
    "solutions": ["solution 1", "solution 2", "solution 3"],
    "impact": "impact assessment",
    "next_steps": ["step 1", "step 2", "step 3"],
    "estimated_resolution_time": "time estimate",
    "confidence": 0.0-1.0
}}"""
    
    def _parse_deep_analysis_response(self, response: str) -> Dict[str, Any]:
        """
        Parse and validate deep analysis response from Mistral AI.
        
        Args:
            response: JSON response string from Mistral
            
        Returns:
            Validated deep analysis dictionary
            
        Raises:
            ValueError: If response is invalid
        """
        try:
            # Strip markdown code blocks if present
            response = response.strip()
            if response.startswith('```'):
                lines = response.split('\n')
                if lines[0].startswith('```'):
                    lines = lines[1:]
                if lines and lines[-1].strip() == '```':
                    lines = lines[:-1]
                response = '\n'.join(lines)
            
            # Parse JSON
            data = json.loads(response)
            
            # Validate and extract fields with defaults
            result = {
                'root_cause': str(data.get('root_cause', 'Analysis in progress...')),
                'solutions': data.get('solutions', []),
                'impact': str(data.get('impact', 'Not assessed')),
                'next_steps': data.get('next_steps', []),
                'estimated_resolution_time': str(data.get('estimated_resolution_time', 'Unknown')),
                'confidence': float(data.get('confidence', 0.7))
            }
            
            # Ensure lists are actually lists
            if not isinstance(result['solutions'], list):
                result['solutions'] = [str(result['solutions'])]
            if not isinstance(result['next_steps'], list):
                result['next_steps'] = [str(result['next_steps'])]
            
            # Clamp confidence to [0, 1]
            result['confidence'] = max(0.0, min(1.0, result['confidence']))
            
            return result
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse deep analysis JSON: {e}")
            raise ValueError(f"Invalid JSON response: {e}")
        except (KeyError, ValueError, TypeError) as e:
            self.logger.error(f"Invalid deep analysis format: {e}")
            raise ValueError(f"Invalid response format: {e}")
    
    def _fallback_deep_analysis(self, ticket: Ticket) -> Dict[str, Any]:
        """
        Generate fallback deep analysis when AI call fails.
        
        Args:
            ticket: Ticket instance
            
        Returns:
            Basic deep analysis dictionary
        """
        self.logger.info(f"Using fallback deep analysis for {ticket.key}")
        
        # Determine category for context
        category = self._fallback_classification(ticket)['category']
        
        # Generate basic analysis based on category
        if category == "TRIRIGA":
            root_cause = "TRIRIGA-related issue detected. Possible causes: authentication, configuration, or integration problems."
            solutions = [
                "Check TRIRIGA user account status and permissions",
                "Review TRIRIGA logs for error messages",
                "Verify TRIRIGA instance connectivity",
                "Check for recent TRIRIGA configuration changes"
            ]
        elif category == "APIC":
            root_cause = "API Connect issue detected. Possible causes: API gateway configuration, authentication, or routing problems."
            solutions = [
                "Review APIC gateway logs and configuration",
                "Check API endpoint connectivity",
                "Verify authentication tokens and credentials",
                "Review APIC routing and load balancer settings"
            ]
        else:
            root_cause = "Application issue detected. Requires further investigation to determine specific cause."
            solutions = [
                "Review application logs for errors",
                "Check system resources and performance",
                "Verify application configuration",
                "Test with different user accounts or environments"
            ]
        
        return {
            'root_cause': root_cause,
            'solutions': solutions,
            'impact': f"Priority: {ticket.priority}. Requires investigation to assess full impact.",
            'next_steps': [
                "Gather detailed logs and error messages",
                "Reproduce the issue in a test environment",
                "Identify affected users and systems",
                "Escalate to appropriate technical team"
            ],
            'estimated_resolution_time': "2-5 days (pending investigation)",
            'confidence': 0.6
        }
    
    def _build_classification_prompt(self, ticket: Ticket) -> str:
        """Build the classification prompt for Mistral AI."""
        return f"""You are an expert IT support ticket classifier. Analyze the following ticket and classify it into one of these categories:
- TRIRIGA: IBM TRIRIGA real estate and facilities management system
- APIC: IBM API Connect for API management
- APPC: Application-related issues (general applications)

Ticket Information:
Key: {ticket.key}
Summary: {ticket.summary}
Description: {ticket.description}
Priority: {ticket.priority}
Comments: {', '.join(ticket.comments) if ticket.comments else 'None'}

Provide your classification with confidence score (0-1) and reasoning.
Respond in JSON format: {{"category": "TRIRIGA|APIC|APPC", "confidence": 0.0-1.0, "reasoning": "explanation"}}"""
    
    def _build_summarization_prompt(self, ticket: Ticket) -> str:
        """Build the summarization prompt for Mistral AI."""
        return f"""You are an expert at summarizing IT support tickets for team communication. Create a concise summary of this ticket for Slack notification.

Ticket Information:
Key: {ticket.key}
Summary: {ticket.summary}
Description: {ticket.description}
Priority: {ticket.priority}
Comments: {', '.join(ticket.comments) if ticket.comments else 'None'}

Provide:
1. A 2-3 sentence summary
2. 3-5 key points (bullet points)
3. Urgency assessment (low/medium/high)

Respond in JSON format: {{"summary": "...", "key_points": ["...", "..."], "urgency": "low|medium|high"}}"""
    
    def _build_combined_prompt(self, ticket: Ticket) -> str:
        """Build the combined analysis prompt for Mistral AI."""
        return f"""You are an expert IT support ticket analyst specializing in IBM enterprise systems. Analyze the following ticket and provide both classification and summary.

Ticket Information:
Key: {ticket.key}
Summary: {ticket.summary}
Description: {ticket.description}
Priority: {ticket.priority}
Comments: {', '.join(ticket.comments) if ticket.comments else 'None'}

Classify into one of these categories:

**TRIRIGA** - IBM TRIRIGA real estate and facilities management system
Key indicators: IMS (Integration Message Service), WO (Work Orders), CAFM systems, Concept, DWP, space management, facilities, real estate, building management, TRIRIGA-specific terms

**APIC** - IBM API Connect for API management
Key indicators: API gateway, API endpoints, REST/SOAP services, API authentication, OAuth, API routing, DataPower, API management console, API policies

**APPC** - General application issues (only if NOT TRIRIGA or APIC)
Use this category only when the issue is clearly not related to TRIRIGA or API Connect

IMPORTANT: If you see terms like IMS, WO, CAFM, Concept, or DWP, it's almost certainly TRIRIGA, not a generic application issue.

Also provide:
1. A 2-3 sentence summary
2. 3-5 key points
3. Urgency assessment (low/medium/high)

Respond in JSON format: {{
    "category": "TRIRIGA|APIC|APPC",
    "confidence": 0.0-1.0,
    "reasoning": "explanation",
    "summary": "...",
    "key_points": ["...", "..."],
    "urgency": "low|medium|high"
}}"""
    
    def _call_mistral_with_retry(
        self,
        prompt: str,
        model: str,
        temperature: float
    ) -> str:
        """
        Call Mistral AI API with retry logic for transient failures.
        
        Args:
            prompt: The prompt to send to Mistral
            model: Model name to use
            temperature: Temperature setting for generation
            
        Returns:
            Response text from Mistral AI
            
        Raises:
            Exception: If all retries fail
        """
        last_exception: Optional[Exception] = None
        delay = self.RETRY_DELAY
        
        for attempt in range(self.MAX_RETRIES):
            try:
                self.logger.debug(
                    f"Calling Mistral AI (attempt {attempt + 1}/{self.MAX_RETRIES})"
                )
                
                response = self.client.chat.complete(
                    model=model,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=temperature
                )
                
                # Extract response text
                if response and response.choices and len(response.choices) > 0:
                    content = response.choices[0].message.content
                    self.logger.debug("Mistral AI call successful")
                    return content
                else:
                    raise ValueError("Empty response from Mistral AI")
                
            except Exception as e:
                last_exception = e
                self.logger.warning(
                    f"Mistral AI call failed (attempt {attempt + 1}/{self.MAX_RETRIES}): {e}"
                )
                
                # Don't retry on the last attempt
                if attempt < self.MAX_RETRIES - 1:
                    self.logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                    delay *= self.RETRY_BACKOFF
        
        # All retries failed
        if last_exception:
            self.logger.error(f"All Mistral AI retry attempts failed: {last_exception}")
            raise last_exception
        else:
            error_msg = "All Mistral AI retry attempts failed with unknown error"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def _parse_classification_response(self, response: str) -> Dict[str, Any]:
        """
        Parse and validate classification response from Mistral AI.
        
        Args:
            response: JSON response string from Mistral
            
        Returns:
            Validated classification dictionary
            
        Raises:
            ValueError: If response is invalid
        """
        try:
            # Strip markdown code blocks if present
            response = response.strip()
            if response.startswith('```'):
                # Remove opening ```json or ```
                lines = response.split('\n')
                if lines[0].startswith('```'):
                    lines = lines[1:]
                # Remove closing ```
                if lines and lines[-1].strip() == '```':
                    lines = lines[:-1]
                response = '\n'.join(lines)
            
            # Parse JSON
            data = json.loads(response)
            
            # Validate required fields
            if 'category' not in data:
                raise ValueError("Missing 'category' field")
            if 'confidence' not in data:
                raise ValueError("Missing 'confidence' field")
            if 'reasoning' not in data:
                raise ValueError("Missing 'reasoning' field")
            
            # Validate category
            category = data['category'].upper()
            if category not in self.CATEGORIES:
                self.logger.warning(
                    f"Invalid category '{category}', defaulting to APPC"
                )
                category = "APPC"
            
            # Validate confidence
            confidence = float(data['confidence'])
            if not 0 <= confidence <= 1:
                self.logger.warning(
                    f"Invalid confidence {confidence}, clamping to [0, 1]"
                )
                confidence = max(0.0, min(1.0, confidence))
            
            return {
                'category': category,
                'confidence': confidence,
                'reasoning': str(data['reasoning'])
            }
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {e}")
            raise ValueError(f"Invalid JSON response: {e}")
        except (KeyError, ValueError, TypeError) as e:
            self.logger.error(f"Invalid response format: {e}")
            raise ValueError(f"Invalid response format: {e}")
    
    def _parse_summarization_response(self, response: str) -> Dict[str, Any]:
        """
        Parse and validate summarization response from Mistral AI.
        
        Args:
            response: JSON response string from Mistral
            
        Returns:
            Validated summarization dictionary
            
        Raises:
            ValueError: If response is invalid
        """
        try:
            # Strip markdown code blocks if present
            response = response.strip()
            if response.startswith('```'):
                lines = response.split('\n')
                if lines[0].startswith('```'):
                    lines = lines[1:]
                if lines and lines[-1].strip() == '```':
                    lines = lines[:-1]
                response = '\n'.join(lines)
            
            # Parse JSON
            data = json.loads(response)
            
            # Validate required fields
            if 'summary' not in data:
                raise ValueError("Missing 'summary' field")
            if 'key_points' not in data:
                raise ValueError("Missing 'key_points' field")
            if 'urgency' not in data:
                raise ValueError("Missing 'urgency' field")
            
            # Validate urgency
            urgency = data['urgency'].lower()
            if urgency not in self.URGENCY_LEVELS:
                self.logger.warning(
                    f"Invalid urgency '{urgency}', defaulting to medium"
                )
                urgency = "medium"
            
            # Validate key_points is a list
            key_points = data['key_points']
            if not isinstance(key_points, list):
                key_points = [str(key_points)]
            
            return {
                'summary': str(data['summary']),
                'key_points': [str(point) for point in key_points],
                'urgency': urgency
            }
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {e}")
            raise ValueError(f"Invalid JSON response: {e}")
        except (KeyError, ValueError, TypeError) as e:
            self.logger.error(f"Invalid response format: {e}")
            raise ValueError(f"Invalid response format: {e}")
    
    def _parse_combined_response(self, response: str) -> Dict[str, Any]:
        """
        Parse and validate combined analysis response from Mistral AI.
        
        Args:
            response: JSON response string from Mistral
            
        Returns:
            Validated combined analysis dictionary
            
        Raises:
            ValueError: If response is invalid
        """
        try:
            # Strip markdown code blocks if present
            response = response.strip()
            if response.startswith('```'):
                lines = response.split('\n')
                if lines[0].startswith('```'):
                    lines = lines[1:]
                if lines and lines[-1].strip() == '```':
                    lines = lines[:-1]
                response = '\n'.join(lines)
            
            # Parse JSON
            data = json.loads(response)
            
            # Validate all required fields
            required_fields = [
                'category', 'confidence', 'reasoning',
                'summary', 'key_points', 'urgency'
            ]
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing '{field}' field")
            
            # Validate and normalize category
            category = data['category'].upper()
            if category not in self.CATEGORIES:
                self.logger.warning(
                    f"Invalid category '{category}', defaulting to APPC"
                )
                category = "APPC"
            
            # Validate confidence
            confidence = float(data['confidence'])
            if not 0 <= confidence <= 1:
                self.logger.warning(
                    f"Invalid confidence {confidence}, clamping to [0, 1]"
                )
                confidence = max(0.0, min(1.0, confidence))
            
            # Validate urgency
            urgency = data['urgency'].lower()
            if urgency not in self.URGENCY_LEVELS:
                self.logger.warning(
                    f"Invalid urgency '{urgency}', defaulting to medium"
                )
                urgency = "medium"
            
            # Validate key_points is a list
            key_points = data['key_points']
            if not isinstance(key_points, list):
                key_points = [str(key_points)]
            
            return {
                'category': category,
                'confidence': confidence,
                'reasoning': str(data['reasoning']),
                'summary': str(data['summary']),
                'key_points': [str(point) for point in key_points],
                'urgency': urgency
            }
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {e}")
            raise ValueError(f"Invalid JSON response: {e}")
        except (KeyError, ValueError, TypeError) as e:
            self.logger.error(f"Invalid response format: {e}")
            raise ValueError(f"Invalid response format: {e}")
    
    def _fallback_classification(self, ticket: Ticket) -> Dict[str, Any]:
        """
        Provide fallback classification based on keyword matching.
        
        Used when AI classification fails.
        
        Args:
            ticket: Ticket to classify
            
        Returns:
            Fallback classification dictionary
        """
        self.logger.info(f"Using fallback classification for {ticket.key}")
        
        # Get full content for keyword matching
        content = ticket.get_full_content().lower()
        
        # Keyword-based classification
        tririga_keywords = ['tririga', 'real estate', 'facilities', 'space management']
        apic_keywords = [
            'api connect', 'apic', 'api gateway', 'api management',
            'api', 'endpoint', 'integration', 'rest', 'soap', 'web service',
            '401', '403', '500', '502', '503', 'unauthorized', 'forbidden',
            'authentication', 'token', 'oauth', 'certificate', 'ssl', 'tls'
        ]
        
        # Count keyword matches
        tririga_score = sum(1 for kw in tririga_keywords if kw in content)
        apic_score = sum(1 for kw in apic_keywords if kw in content)
        
        # Determine category
        if tririga_score > apic_score:
            category = "TRIRIGA"
            confidence = min(0.7, 0.5 + tririga_score * 0.1)
            reasoning = "Fallback classification based on TRIRIGA keywords"
        elif apic_score > 0:
            category = "APIC"
            confidence = min(0.7, 0.5 + apic_score * 0.1)
            reasoning = "Fallback classification based on APIC keywords"
        else:
            category = "APPC"
            confidence = 0.5
            reasoning = "Fallback classification - no specific keywords found"
        
        return {
            'category': category,
            'confidence': confidence,
            'reasoning': reasoning
        }
    
    def _fallback_summarization(self, ticket: Ticket) -> Dict[str, Any]:
        """
        Provide fallback summarization based on ticket fields.
        
        Used when AI summarization fails.
        
        Args:
            ticket: Ticket to summarize
            
        Returns:
            Fallback summarization dictionary
        """
        self.logger.info(f"Using fallback summarization for {ticket.key}")
        
        # Create basic summary from ticket fields
        summary = f"{ticket.key}: {ticket.summary}"
        if ticket.description:
            # Add first sentence of description
            first_sentence = ticket.description.split('.')[0]
            summary += f". {first_sentence}."
        
        # Extract key points
        key_points = [ticket.summary]
        if ticket.description:
            key_points.append(f"Description: {ticket.description[:100]}...")
        if ticket.comments:
            key_points.append(f"{len(ticket.comments)} comment(s)")
        if ticket.attachments:
            key_points.append(f"{len(ticket.attachments)} attachment(s)")
        
        # Determine urgency from priority
        priority_lower = ticket.priority.lower()
        if priority_lower in ['highest', 'critical', 'blocker']:
            urgency = "high"
        elif priority_lower in ['high']:
            urgency = "medium"
        else:
            urgency = "low"
        
        return {
            'summary': summary,
            'key_points': key_points[:5],  # Limit to 5 points
            'urgency': urgency
        }


# Made with Bob