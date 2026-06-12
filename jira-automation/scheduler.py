"""
Scheduler for running JIRA automation periodically.

This script runs the automation at regular intervals, suitable for
deployment on cloud platforms like Heroku, Railway, or Render.
"""

import schedule
import time
import subprocess
import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def run_automation():
    """
    Run the JIRA automation script.
    
    Executes main.py with configured parameters and logs the results.
    """
    logger.info("="*70)
    logger.info(f"Starting scheduled automation run at {datetime.now()}")
    logger.info("="*70)
    
    try:
        # Run the automation
        result = subprocess.run(
            ["python", "main.py", "--max-tickets", "10"],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        # Log output
        if result.stdout:
            logger.info("Automation output:")
            for line in result.stdout.split('\n'):
                if line.strip():
                    logger.info(f"  {line}")
        
        # Check for errors
        if result.returncode != 0:
            logger.error(f"Automation failed with exit code {result.returncode}")
            if result.stderr:
                logger.error("Error output:")
                for line in result.stderr.split('\n'):
                    if line.strip():
                        logger.error(f"  {line}")
        else:
            logger.info("Automation completed successfully")
            
    except subprocess.TimeoutExpired:
        logger.error("Automation timed out after 5 minutes")
    except Exception as e:
        logger.error(f"Error running automation: {e}", exc_info=True)
    
    logger.info("="*70)
    logger.info(f"Scheduled run completed at {datetime.now()}")
    logger.info("="*70)


def main():
    """
    Main scheduler loop.
    
    Schedules the automation to run every hour and keeps the process alive.
    """
    logger.info("="*70)
    logger.info("JIRA Automation Scheduler Started")
    logger.info("="*70)
    logger.info("Schedule: Every hour")
    logger.info("Max tickets per run: 10")
    logger.info("="*70)
    
    # Schedule to run every hour
    schedule.every().hour.do(run_automation)
    
    # Also schedule specific times if needed (optional)
    # schedule.every().day.at("09:00").do(run_automation)  # 9 AM daily
    # schedule.every().day.at("14:00").do(run_automation)  # 2 PM daily
    
    # Run immediately on start
    logger.info("Running initial automation...")
    run_automation()
    
    # Keep running
    logger.info("Scheduler is now running. Press Ctrl+C to stop.")
    logger.info("="*70)
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("\nScheduler stopped by user")
    except Exception as e:
        logger.error(f"Scheduler error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()

# Made with Bob
