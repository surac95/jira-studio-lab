"""Test script to check Mistral AI response format."""
from services.ai_service import AIService
from config import get_settings
from services.jira_service import JiraService

# Initialize services
settings = get_settings()
ai_service = AIService(settings)
jira_service = JiraService(settings)

# Fetch a real ticket
print("Fetching ticket ITSD-333560...")
tickets = jira_service.get_new_tickets(max_results=1)

if tickets:
    ticket = tickets[0]
    print(f"\nTicket: {ticket.key}")
    print(f"Summary: {ticket.summary}")
    
    # Build prompt
    prompt = ai_service._build_combined_prompt(ticket)
    print(f"\n{'='*70}")
    print("PROMPT:")
    print(f"{'='*70}")
    print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
    
    # Call Mistral AI
    print(f"\n{'='*70}")
    print("Calling Mistral AI...")
    print(f"{'='*70}")
    
    try:
        response = ai_service._call_mistral_with_retry(
            prompt=prompt,
            model="mistral-large-latest",
            temperature=0.3
        )
        
        print(f"\n{'='*70}")
        print("RAW RESPONSE:")
        print(f"{'='*70}")
        print(response)
        print(f"\n{'='*70}")
        
        # Try to parse using the service's method
        try:
            parsed = ai_service._parse_combined_response(response)
            print("\nPARSED JSON:")
            import json
            print(json.dumps(parsed, indent=2))
        except Exception as e:
            print(f"\nPARSE ERROR: {e}")
            print(f"Response type: {type(response)}")
            print(f"Response length: {len(response)}")
            
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
else:
    print("No tickets found!")

# Made with Bob
