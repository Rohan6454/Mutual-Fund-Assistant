"""
Long-running scheduler: daily scrape → chunk → embed (subprocess pipeline).

Uses APScheduler with cron from config (SCHEDULER_CRON_HOUR, SCHEDULER_CRON_MINUTE, SCHEDULER_TIMEZONE).
GitHub Actions scheduling is defined under .github/workflows/ (see phase-1 README).

Usage:
  python phase-1-data-collection/scheduler_service.py              # blocking cron
  python phase-1-data-collection/scheduler_service.py --run-now      # single run, exit
"""

from __future__ import annotations

import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from zoneinfo import ZoneInfo

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from config.settings import settings

# Create logs directory if it doesn't exist
logs_dir = REPO_ROOT / "logs"
logs_dir.mkdir(exist_ok=True)

# Setup comprehensive logging
log_file = logs_dir / f"scheduler_{datetime.now().strftime('%Y%m%d')}.log"

# Configure logging with both console and file output
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def run_daily_pipeline() -> None:
    """Run the complete daily ingestion pipeline with detailed logging."""
    start_time = datetime.now()
    logger.info("=" * 80)
    logger.info("Starting daily pipeline execution at %s", start_time.isoformat())
    logger.info("=" * 80)
    
    py = sys.executable
    phases = [
        {
            "name": "Phase 1: Data Collection",
            "script": REPO_ROOT / "phase-1-data-collection" / "scrape_sources.py",
            "description": "Scraping sources from data/sources.json"
        },
        {
            "name": "Phase 2: Document Processing", 
            "script": REPO_ROOT / "phase-2-document-processing" / "process_documents.py",
            "description": "Processing raw documents into chunks"
        },
        {
            "name": "Phase 2: Embedding Generation",
            "script": REPO_ROOT / "phase-2-document-processing" / "generate_embeddings.py", 
            "description": "Generating embeddings and updating Qdrant"
        }
    ]
    
    success_count = 0
    total_count = len(phases)
    
    for i, phase in enumerate(phases, 1):
        phase_start = datetime.now()
        logger.info(f"Phase {i}/{total_count}: {phase['name']}")
        logger.info(f"Description: {phase['description']}")
        logger.info(f"Script: {phase['script']}")
        logger.info(f"Starting at: {phase_start.isoformat()}")
        
        try:
            result = subprocess.run(
                [py, str(phase['script'])], 
                cwd=str(REPO_ROOT), 
                check=True,
                capture_output=True, 
                text=True,
                timeout=3600  # 1 hour timeout per phase
            )
            
            phase_end = datetime.now()
            phase_duration = (phase_end - phase_start).total_seconds()
            
            logger.info(f"Phase {i} completed successfully in {phase_duration:.2f} seconds")
            logger.info(f"Phase {i} stdout: {result.stdout[-500:] if len(result.stdout) > 500 else result.stdout}")
            success_count += 1
            
        except subprocess.TimeoutExpired:
            logger.error(f"Phase {i} timed out after 1 hour")
            logger.error(f"Failed script: {phase['script']}")
            break
            
        except subprocess.CalledProcessError as e:
            phase_end = datetime.now()
            phase_duration = (phase_end - phase_start).total_seconds()
            logger.error(f"Phase {i} failed after {phase_duration:.2f} seconds")
            logger.error(f"Failed script: {phase['script']}")
            logger.error(f"Return code: {e.returncode}")
            logger.error(f"Stdout: {e.stdout}")
            logger.error(f"Stderr: {e.stderr}")
            break
            
        except Exception as e:
            logger.error(f"Phase {i} encountered unexpected error: {e}")
            logger.error(f"Failed script: {phase['script']}")
            break
    
    end_time = datetime.now()
    total_duration = (end_time - start_time).total_seconds()
    
    logger.info("=" * 80)
    logger.info("Daily pipeline execution summary:")
    logger.info(f"Started: {start_time.isoformat()}")
    logger.info(f"Completed: {end_time.isoformat()}")
    logger.info(f"Total duration: {total_duration:.2f} seconds")
    logger.info(f"Phases completed: {success_count}/{total_count}")
    logger.info(f"Status: {'SUCCESS' if success_count == total_count else 'PARTIAL_FAILURE'}")
    logger.info("=" * 80)


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "--run-now":
        run_daily_pipeline()
        return

    if not settings.SCHEDULER_ENABLED:
        logger.info("SCHEDULER_ENABLED is false; exiting.")
        return

    try:
        tz = ZoneInfo(settings.SCHEDULER_TIMEZONE)
    except Exception:
        logger.exception("Invalid SCHEDULER_TIMEZONE %r", settings.SCHEDULER_TIMEZONE)
        raise

    scheduler = BlockingScheduler(timezone=tz)
    scheduler.add_job(
        run_daily_pipeline,
        CronTrigger(
            hour=settings.SCHEDULER_CRON_HOUR,
            minute=settings.SCHEDULER_CRON_MINUTE,
            timezone=tz,
        ),
        id="mutual_fund_faq_daily_ingest",
        replace_existing=True,
    )
    logger.info(
        "Scheduler running: daily at %02d:%02d %s (Ctrl+C to stop)",
        settings.SCHEDULER_CRON_HOUR,
        settings.SCHEDULER_CRON_MINUTE,
        settings.SCHEDULER_TIMEZONE,
    )
    scheduler.start()


if __name__ == "__main__":
    main()
