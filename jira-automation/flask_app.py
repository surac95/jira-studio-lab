"""
Flask web endpoint for triggering JIRA automation.

This creates HTTP endpoints that can be called by cloud cron services
like cron-job.org, EasyCron, or similar platforms.

Deploy this to PythonAnywhere, Heroku, Render, or any Python hosting.
"""

from flask import Flask, jsonify, request
import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from main import TicketOrchestrator
from config import get_settings
from utils.logger import get_logger

app = Flask(__name__)
logger = get_logger(__name__)

# Security: Secret token for authentication
# Set this in your environment variables
SECRET_TOKEN = os.getenv('WEBHOOK_SECRET', 'change-this-secret-token-in-production')

def verify_token():
    """Verify the secret token from request headers."""
    token = request.headers.get('X-Secret-Token')
    if token != SECRET_TOKEN:
        logger.warning(f"Unauthorized access attempt from {request.remote_addr}")
        return False
    return True


@app.route('/')
def home():
    """
    Home page with service information.
    
    Returns:
        JSON with service status and available endpoints
    """
    return jsonify({
        'service': 'JIRA Automation System',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'POST /trigger': 'Trigger automation workflow',
            'GET /health': 'Health check',
            'GET /status': 'Team status',
            'GET /stats': 'Assignment statistics'
        },
        'documentation': 'See CLOUD_CRON_DEPLOYMENT.md for setup instructions'
    })


@app.route('/trigger', methods=['POST'])
def trigger_automation():
    """
    Trigger the automation workflow.
    
    Request Headers:
        X-Secret-Token: Authentication token
    
    Request Body (JSON, optional):
        {
            "dry_run": false,
            "max_tickets": 50
        }
    
    Returns:
        JSON with execution statistics
    """
    # Verify authentication
    if not verify_token():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # Get parameters from request
        data = request.get_json() or {}
        dry_run = data.get('dry_run', False)
        max_tickets = data.get('max_tickets', None)
        
        logger.info(f"Triggering automation (dry_run={dry_run}, max_tickets={max_tickets})")
        
        # Initialize and run orchestrator
        settings = get_settings()
        orchestrator = TicketOrchestrator(settings)
        stats = orchestrator.run(dry_run=dry_run, max_tickets=max_tickets)
        
        logger.info(f"Automation completed: {stats['tickets_assigned']} tickets assigned")
        
        return jsonify({
            'status': 'success',
            'message': 'Automation completed successfully',
            'stats': {
                'tickets_fetched': stats['tickets_fetched'],
                'tickets_analyzed': stats['tickets_analyzed'],
                'tickets_assigned': stats['tickets_assigned'],
                'tickets_failed': stats['tickets_failed'],
                'execution_time': round(stats.get('execution_time', 0), 2),
                'by_category': stats.get('by_category', {})
            },
            'dry_run': dry_run
        })
        
    except Exception as e:
        logger.error(f"Automation failed: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Automation failed',
            'error': str(e)
        }), 500


@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.
    
    Tests connections to all external services (JIRA, Slack, AI).
    
    Returns:
        JSON with health status and connection test results
    """
    try:
        logger.info("Running health check")
        
        settings = get_settings()
        orchestrator = TicketOrchestrator(settings)
        connections = orchestrator.test_connections()
        
        all_healthy = all(connections.values())
        status_code = 200 if all_healthy else 503
        
        return jsonify({
            'status': 'healthy' if all_healthy else 'degraded',
            'connections': {
                'jira': 'ok' if connections['jira'] else 'failed',
                'slack': 'ok' if connections['slack'] else 'failed',
                'ai': 'ok' if connections['ai'] else 'failed'
            },
            'message': 'All systems operational' if all_healthy else 'Some services unavailable'
        }), status_code
        
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'message': 'Health check failed'
        }), 500


@app.route('/status', methods=['GET'])
def team_status():
    """
    Get current team workload status.
    
    Returns:
        JSON with team member workload and statistics
    """
    try:
        logger.info("Fetching team status")
        
        settings = get_settings()
        orchestrator = TicketOrchestrator(settings)
        status = orchestrator.get_team_status()
        
        return jsonify({
            'status': 'success',
            'team_members': status['team_members'],
            'statistics': status['statistics']
        })
        
    except Exception as e:
        logger.error(f"Failed to get team status: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e),
            'message': 'Failed to retrieve team status'
        }), 500


@app.route('/stats', methods=['GET'])
def assignment_statistics():
    """
    Get assignment statistics.
    
    Returns:
        JSON with detailed assignment statistics by category
    """
    try:
        logger.info("Fetching assignment statistics")
        
        settings = get_settings()
        orchestrator = TicketOrchestrator(settings)
        
        # Get workload service statistics
        from services import WorkloadService
        workload_service = WorkloadService(settings)
        stats = workload_service.get_assignment_statistics()
        
        return jsonify({
            'status': 'success',
            'statistics': stats
        })
        
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e),
            'message': 'Failed to retrieve statistics'
        }), 500


@app.route('/test', methods=['GET'])
def test_endpoint():
    """
    Simple test endpoint to verify the service is running.
    
    Returns:
        JSON with test message
    """
    return jsonify({
        'status': 'ok',
        'message': 'Service is running',
        'timestamp': str(Path(__file__).stat().st_mtime)
    })


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'status': 'error',
        'message': 'Endpoint not found',
        'available_endpoints': [
            'GET /',
            'POST /trigger',
            'GET /health',
            'GET /status',
            'GET /stats',
            'GET /test'
        ]
    })


@app.route('/slack/interactive', methods=['POST'])
def handle_slack_interaction():
    """
    Handle Slack interactive button clicks.
    
    This endpoint receives button click events from Slack and processes them.
    Slack sends the payload as form data with a 'payload' field containing JSON.
    
    Returns:
        Empty response (200 OK) - Slack requires quick response
    """
    try:
        import json
        from services.jira_service import JiraService
        from services.ai_service import AIService
        from services.slack_service import SlackService
        
        # Parse the payload from Slack
        payload_str = request.form.get('payload')
        if not payload_str:
            logger.error("No payload in Slack interaction request")
            return '', 400
        
        payload = json.loads(payload_str)
        logger.info(f"Received Slack interaction: {payload.get('type')}")
        
        # Extract action information
        actions = payload.get('actions', [])
        if not actions:
            logger.error("No actions in Slack payload")
            return '', 400
        
        action = actions[0]
        action_id = action.get('action_id')
        ticket_key = action.get('value')
        response_url = payload.get('response_url')
        
        logger.info(f"Processing action: {action_id} for ticket: {ticket_key}")
        
        # Handle different button actions
        if action_id == 'deep_analysis':
            # User clicked "Get Deep Analysis" button
            handle_deep_analysis_request(ticket_key, response_url)
        
        elif action_id == 'reanalyze' or action_id == 'reanalyze_deep':
            # User clicked "Re-analyze" button
            handle_reanalyze_request(ticket_key, response_url)
        
        else:
            logger.warning(f"Unknown action_id: {action_id}")
        
        # Return 200 OK immediately (Slack requires quick response)
        return '', 200
        
    except Exception as e:
        logger.error(f"Error handling Slack interaction: {e}", exc_info=True)
        return '', 500


def handle_deep_analysis_request(ticket_key: str, response_url: str):
    """
    Handle deep analysis button click.
    
    This runs in the background after returning 200 to Slack.
    
    Args:
        ticket_key: JIRA ticket key
        response_url: Slack response URL for sending the analysis
    """
    try:
        from services.jira_service import JiraService
        from services.ai_service import AIService
        from services.slack_service import SlackService
        
        logger.info(f"Starting deep analysis for {ticket_key}")
        
        # Initialize services
        settings = get_settings()
        jira_service = JiraService(settings)
        ai_service = AIService(settings)
        slack_service = SlackService(settings)
        
        # Fetch the ticket from JIRA
        client = jira_service._get_client()
        jira_issue = client.issue(ticket_key)
        
        # Convert to our Ticket model
        from models.ticket import Ticket
        ticket = Ticket.from_jira_issue(jira_issue)
        
        # Perform deep analysis
        deep_analysis = ai_service.analyze_ticket_deep(ticket)
        
        # Send analysis back to Slack
        slack_service.send_deep_analysis_response(
            ticket_key,
            deep_analysis,
            response_url
        )
        
        logger.info(f"Deep analysis completed and sent for {ticket_key}")
        
    except Exception as e:
        logger.error(f"Error in deep analysis for {ticket_key}: {e}", exc_info=True)
        # Send error message to Slack
        try:
            import requests
            requests.post(
                response_url,
                json={
                    "text": f"❌ Error performing deep analysis for {ticket_key}: {str(e)}"
                }
            )
        except:
            pass


def handle_reanalyze_request(ticket_key: str, response_url: str):
    """
    Handle re-analyze button click.
    
    Args:
        ticket_key: JIRA ticket key
        response_url: Slack response URL
    """
    try:
        from services.jira_service import JiraService
        from services.ai_service import AIService
        
        logger.info(f"Re-analyzing ticket {ticket_key}")
        
        # Initialize services
        settings = get_settings()
        jira_service = JiraService(settings)
        ai_service = AIService(settings)
        
        # Fetch the ticket from JIRA (gets latest comments)
        client = jira_service._get_client()
        jira_issue = client.issue(ticket_key)
        
        # Convert to our Ticket model
        from models.ticket import Ticket
        ticket = Ticket.from_jira_issue(jira_issue)
        
        # Perform analysis
        analysis = ai_service.analyze_ticket(ticket)
        
        # Send updated analysis to Slack
        import requests
        requests.post(
            response_url,
            json={
                "text": f"🔄 Re-analysis for {ticket_key}:\n"
                        f"Category: {analysis['category']} ({analysis['confidence']:.0%} confidence)\n"
                        f"Urgency: {analysis['urgency']}\n"
                        f"Summary: {analysis['summary']}"
            }
        )
        
        logger.info(f"Re-analysis completed for {ticket_key}")
        
    except Exception as e:
        logger.error(f"Error re-analyzing {ticket_key}: {e}", exc_info=True)
        try:
            import requests
            requests.post(
                response_url,
                json={"text": f"❌ Error re-analyzing {ticket_key}: {str(e)}"}
            )
        except:
            pass


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'status': 'error',
        'message': 'Internal server error',
        'error': str(error)
    }), 500


# For local testing
if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("JIRA Automation System - Flask Web Service")
    print("=" * 70)
    print("\nStarting development server...")
    print("Available endpoints:")
    print("  GET  /           - Service information")
    print("  POST /trigger    - Trigger automation (requires X-Secret-Token header)")
    print("  GET  /health     - Health check")
    print("  GET  /status     - Team status")
    print("  GET  /stats      - Assignment statistics")
    print("  GET  /test       - Test endpoint")
    print("\nSecurity:")
    print(f"  Secret Token: {SECRET_TOKEN}")
    print("  Set WEBHOOK_SECRET environment variable in production!")
    print("\n" + "=" * 70 + "\n")
    
    # Run development server
    app.run(debug=True, host='0.0.0.0', port=5000)


# Made with Bob