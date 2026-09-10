# download_manager.py — Download queue manager

import threading
from collections import deque


class DownloadJob:
    """Represents a single download job."""
    def __init__(self, video, format_type='mp4', quality='Auto',
                 start_time=None, end_time=None, output_path='.', cookies_browser=None):
        self.video = video
        self.format_type = format_type
        self.quality = quality
        self.start_time = start_time
        self.end_time = end_time
        self.output_path = output_path
        self.file_path = output_path
        self.cookies_browser = cookies_browser
        self.status = 'waiting'  # waiting, downloading, completed, failed
        self.progress = 0
        self.speed = ''
        self.error = None
        self.title = video.get('title', 'Untitled')


class DownloadManager:
    """
    Manages a queue of download jobs, processing them sequentially.
    """
    def __init__(self, download_fn):
        self.download_fn = download_fn  # backend.download_video function
        self.queue = deque()
        self.current_job = None
        self._lock = threading.Lock()
        self._processing = False

        # Callbacks
        self.on_queue_update = None   # Called when queue state changes
        self.on_job_complete = None   # Called with (job) when a job completes
        self.on_job_error = None      # Called with (job, error_msg)

    def add_job(self, job):
        """Add a download job to the queue."""
        with self._lock:
            self.queue.append(job)
        if self.on_queue_update:
            self.on_queue_update()
        self._process_next()

    def get_all_jobs(self):
        """Return list of all jobs (current + queued)."""
        jobs = []
        with self._lock:
            if self.current_job:
                jobs.append(self.current_job)
            jobs.extend(self.queue)
        return jobs

    def clear_completed(self):
        """Remove completed/failed jobs. They're not in the deque anymore, so this is a no-op for the queue."""
        pass  # completed jobs are already removed from queue

    def _process_next(self):
        """Start processing the next job in the queue if not already processing."""
        with self._lock:
            if self._processing or not self.queue:
                return
            self._processing = True
            self.current_job = self.queue.popleft()
            self.current_job.status = 'downloading'

        if self.on_queue_update:
            self.on_queue_update()

        job = self.current_job
        self.download_fn(
            url=job.video['url'],
            output_path=job.output_path,
            format_type=job.format_type,
            quality=job.quality,
            start_time=job.start_time,
            end_time=job.end_time,
            cookies_browser=job.cookies_browser,
            progress_callback=lambda p: self._on_progress(job, p),
            speed_callback=lambda s: self._on_speed(job, s),
            completion_callback=lambda title, file_path=None: self._on_complete(job, title, file_path),
            error_callback=lambda e: self._on_error(job, e),
        )

    def _on_progress(self, job, percent):
        job.progress = percent
        if self.on_queue_update:
            self.on_queue_update()

    def _on_speed(self, job, speed_str):
        job.speed = speed_str

    def _on_complete(self, job, title, file_path=None):
        job.status = 'completed'
        job.progress = 100
        if file_path:
            job.file_path = file_path
        with self._lock:
            self._processing = False
            self.current_job = None
        if self.on_job_complete:
            self.on_job_complete(job)
        if self.on_queue_update:
            self.on_queue_update()
        self._process_next()

    def _on_error(self, job, error_msg):
        job.status = 'failed'
        job.error = error_msg
        with self._lock:
            self._processing = False
            self.current_job = None
        if self.on_job_error:
            self.on_job_error(job, error_msg)
        if self.on_queue_update:
            self.on_queue_update()
        self._process_next()
