import logging
from apscheduler.schedulers.background import BackgroundScheduler
from scraper import PriceScraperEngine

logger = logging.getLogger("PriceScheduler")

scheduler = None

def init_scheduler(app, db):
    global scheduler
    if scheduler is not None and scheduler.running:
        return scheduler

    scheduler = BackgroundScheduler(daemon=True)
    
    # Schedule automated background price scraping every 3 hours
    scheduler.add_job(
        func=PriceScraperEngine.run_full_scraping_job,
        args=[app, db.session],
        trigger="interval",
        hours=3,
        id="automated_price_scraper",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("APScheduler initialized: Automated price scraping running every 3 hours.")
    return scheduler
