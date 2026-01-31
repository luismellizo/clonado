import asyncio
from app.celery_app import app
from app.cloner import ClonerPro
from app.utils import create_zip_archive
import os
import shutil
import logging

logger = logging.getLogger(__name__)


@app.task(bind=True)
def clone_site_task(self, url, job_id):
    """Celery task to clone a website with full analysis."""
    
    self.update_state(state='PROGRESS', meta={'status': 'Initializing...', 'progress': 5})
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        # Path configuration
        base_download_dir = "/app/downloads"
        
        # Initialize cloner
        self.update_state(state='PROGRESS', meta={'status': 'Starting browser...', 'progress': 10})
        cloner = ClonerPro(url, job_id, output_base_dir=base_download_dir)
        
        # Create progress callback wrapper
        async def run_with_progress():
            self.update_state(state='PROGRESS', meta={'status': 'Navigating to site...', 'progress': 15})
            await cloner.capture_site()
        
        # Run the async capture
        self.update_state(state='PROGRESS', meta={'status': 'Loading page content...', 'progress': 20})
        loop.run_until_complete(run_with_progress())
        
        # Get analysis data
        self.update_state(state='PROGRESS', meta={'status': 'Generating reports...', 'progress': 85})
        analysis = cloner.get_analysis()
        
        # Create ZIP archive
        self.update_state(state='PROGRESS', meta={'status': 'Compressing files...', 'progress': 90})
        zip_path = os.path.join(base_download_dir, f"{job_id}.zip")
        create_zip_archive(cloner.output_dir, zip_path)
        
        # Clean up the uncompressed folder (optional, keep for analysis endpoint)
        # shutil.rmtree(cloner.output_dir)
        
        self.update_state(state='PROGRESS', meta={'status': 'Complete!', 'progress': 100})
        
        return {
            'status': 'Completed',
            'zip_path': str(zip_path),
            'job_id': job_id,
            'analysis': analysis
        }
        
    except Exception as e:
        logger.error(f"Task failed: {e}")
        self.update_state(state='FAILURE', meta={'status': 'Error', 'error': str(e)})
        raise e
