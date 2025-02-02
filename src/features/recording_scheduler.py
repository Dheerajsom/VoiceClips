# src/features/recording_scheduler.py
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))
import threading
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import json
from pathlib import Path
import queue

from src.constants import *
from src.utils.error_handler import ErrorHandler

class RecordingState(Enum):
    """Recording states."""
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

@dataclass
class RecordingTask:
    """Represents a scheduled recording task."""
    id: str
    name: str
    start_time: datetime
    duration: Optional[timedelta]
    repeat_type: str = "none"  # none, daily, weekly, custom
    repeat_interval: Optional[timedelta] = None
    repeat_days: List[int] = field(default_factory=list)  # 0-6 for weekly repeats
    end_date: Optional[datetime] = None
    settings: Dict = field(default_factory=dict)
    state: RecordingState = RecordingState.SCHEDULED
    error: Optional[str] = None
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None

class RecordingScheduler:
    """Manages scheduled recordings."""
    
    def __init__(self, recording_callback: Callable):
        self.logger = logging.getLogger(__name__)
        self.error_handler = ErrorHandler(DEFAULT_LOGS_PATH)
        self.recording_callback = recording_callback
        self.scheduled_recordings: Dict[str, RecordingTask] = {}
        self.active_timers: Dict[str, threading.Timer] = {}
        self.lock = threading.Lock()
        self._running = False
        self._scheduler_thread: Optional[threading.Thread] = None

    def start(self):
        """Start the scheduler."""
        if self._running:
            return

        self._running = True
        self._scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            daemon=True
        )
        self._scheduler_thread.start()
        self.logger.info("Recording scheduler started")

    def stop(self):
        """Stop the scheduler."""
        self._running = False
        if self._scheduler_thread:
            self._scheduler_thread.join()
        self._cancel_all_recordings()
        self.logger.info("Recording scheduler stopped")

    def schedule_recording(self, name: str, start_time: datetime,
                         duration: Optional[timedelta] = None,
                         settings: Dict = None) -> Optional[str]:
        """Schedule a one-time recording."""
        try:
            recording_id = f"rec_{int(time.time())}_{len(self.scheduled_recordings)}"
            
            task = RecordingTask(
                id=recording_id,
                name=name,
                start_time=start_time,
                duration=duration,
                settings=settings or {},
                next_run=start_time
            )
            
            with self.lock:
                self.scheduled_recordings[recording_id] = task
                self._schedule_task(task)
                
            self.logger.info(f"Scheduled recording: {name}")
            return recording_id
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Scheduling recording")
            return None

    def add_recurring_recording(self, name: str, start_time: datetime,
                              duration: timedelta, repeat_type: str,
                              repeat_interval: Optional[timedelta] = None,
                              repeat_days: List[int] = None,
                              end_date: Optional[datetime] = None,
                              settings: Dict = None) -> Optional[str]:
        """Schedule a recurring recording."""
        try:
            recording_id = f"rec_{int(time.time())}_{len(self.scheduled_recordings)}"
            
            task = RecordingTask(
                id=recording_id,
                name=name,
                start_time=start_time,
                duration=duration,
                repeat_type=repeat_type,
                repeat_interval=repeat_interval,
                repeat_days=repeat_days or [],
                end_date=end_date,
                settings=settings or {}
            )
            
            task.next_run = self._calculate_next_run(task)
            
            with self.lock:
                self.scheduled_recordings[recording_id] = task
                self._schedule_task(task)
                
            self.logger.info(f"Added recurring recording: {name}")
            return recording_id
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Adding recurring recording")
            return None

    def _schedule_task(self, task: RecordingTask):
        """Schedule timer for task."""
        try:
            if not task.next_run:
                return

            delay = (task.next_run - datetime.now()).total_seconds()
            if delay < 0:
                return

            timer = threading.Timer(
                delay,
                self._start_recording,
                args=[task]
            )
            timer.daemon = True
            timer.start()
            
            self.active_timers[f"{task.id}_start"] = timer
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Scheduling task")

    def _start_recording(self, task: RecordingTask):
        """Start a scheduled recording."""
        try:
            task.state = RecordingState.RUNNING
            task.last_run = datetime.now()
            
            # Start recording through callback
            self.recording_callback(True, task.settings)
            
            # Schedule stop if duration specified
            if task.duration:
                stop_timer = threading.Timer(
                    task.duration.total_seconds(),
                    self._stop_recording,
                    args=[task]
                )
                stop_timer.daemon = True
                stop_timer.start()
                self.active_timers[f"{task.id}_stop"] = stop_timer
            
            # Schedule next run if recurring
            if task.repeat_type != "none":
                task.next_run = self._calculate_next_run(task)
                if task.next_run:
                    self._schedule_task(task)
            
            self.logger.info(f"Started recording {task.id}")
            
        except Exception as e:
            task.state = RecordingState.FAILED
            task.error = str(e)
            self.error_handler.handle_error(e, context="Starting recording")

    def _stop_recording(self, task: RecordingTask):
        """Stop a running recording."""
        try:
            # Stop recording through callback
            self.recording_callback(False)
            
            task.state = RecordingState.COMPLETED
            
            # Clean up timer
            timer_key = f"{task.id}_stop"
            if timer_key in self.active_timers:
                del self.active_timers[timer_key]
            
            self.logger.info(f"Stopped recording {task.id}")
            
        except Exception as e:
            task.state = RecordingState.FAILED
            task.error = str(e)
            self.error_handler.handle_error(e, context="Stopping recording")

    def _scheduler_loop(self):
        """Main scheduler loop."""
        while self._running:
            try:
                current_time = datetime.now()
                
                with self.lock:
                    # Check for recordings that should start
                    for task in self.scheduled_recordings.values():
                        if (task.state == RecordingState.SCHEDULED and
                            task.next_run and
                            task.next_run <= current_time):
                            self._start_recording(task)
                
                time.sleep(1)  # Check every second
                
            except Exception as e:
                self.error_handler.handle_error(e, context="Scheduler loop")
                time.sleep(5)  # Wait longer on error

    def _cancel_all_recordings(self):
        """Cancel all scheduled recordings."""
        with self.lock:
            for timer in self.active_timers.values():
                timer.cancel()
            self.active_timers.clear()
            
            for task in self.scheduled_recordings.values():
                if task.state in [RecordingState.SCHEDULED, RecordingState.RUNNING]:
                    task.state = RecordingState.CANCELLED
    def modify_recording(self, recording_id: str, **kwargs) -> bool:
        """Modify scheduled recording."""
        try:
            with self.lock:
                if recording_id not in self.scheduled_recordings:
                    return False
                    
                task = self.scheduled_recordings[recording_id]
                
                # Update task attributes
                for key, value in kwargs.items():
                    if hasattr(task, key):
                        setattr(task, key, value)
                
                # Recalculate next run if needed
                if any(key in kwargs for key in ['start_time', 'repeat_type', 
                                               'repeat_interval', 'repeat_days']):
                    task.next_run = self._calculate_next_run(task)
                    self._reschedule_task(task)
                
                return True
                
        except Exception as e:
            self.error_handler.handle_error(e, context="Modifying recording")
            return False

    def _reschedule_task(self, task: RecordingTask):
        """Reschedule a task after modification."""
        try:
            # Cancel existing timer
            timer_key = f"{task.id}_start"
            if timer_key in self.active_timers:
                self.active_timers[timer_key].cancel()
                del self.active_timers[timer_key]
            
            # Schedule new timer
            self._schedule_task(task)
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Rescheduling task")

    def get_upcoming_recordings(self, limit: int = 10) -> List[Dict]:
        """Get list of upcoming recordings."""
        try:
            upcoming = []
            now = datetime.now()
            
            for task in self.scheduled_recordings.values():
                if task.next_run and task.next_run > now:
                    upcoming.append({
                        'id': task.id,
                        'name': task.name,
                        'start_time': task.next_run,
                        'duration': task.duration,
                        'repeat_type': task.repeat_type,
                        'state': task.state.value
                    })
            
            # Sort by start time and limit
            upcoming.sort(key=lambda x: x['start_time'])
            return upcoming[:limit]
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Getting upcoming recordings")
            return []

    def export_schedule(self, filepath: str) -> bool:
        """Export recording schedule to file."""
        try:
            schedule_data = {
                'recordings': [asdict(task) for task in self.scheduled_recordings.values()]
            }
            
            with open(filepath, 'w') as f:
                json.dump(schedule_data, f, indent=2, default=str)
                
            return True
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Exporting schedule")
            return False

    def import_schedule(self, filepath: str) -> bool:
        """Import recording schedule from file."""
        try:
            with open(filepath, 'r') as f:
                schedule_data = json.load(f)
            
            with self.lock:
                # Clear existing schedule
                self._cancel_all_recordings()
                self.scheduled_recordings.clear()
                
                # Import new schedule
                for task_data in schedule_data['recordings']:
                    # Convert string dates to datetime
                    task_data['start_time'] = datetime.fromisoformat(task_data['start_time'])
                    if task_data['end_date']:
                        task_data['end_date'] = datetime.fromisoformat(task_data['end_date'])
                    if task_data['duration']:
                        task_data['duration'] = timedelta(seconds=task_data['duration'])
                    if task_data['repeat_interval']:
                        task_data['repeat_interval'] = timedelta(
                            seconds=task_data['repeat_interval']
                        )
                    
                    task = RecordingTask(**task_data)
                    self.scheduled_recordings[task.id] = task
                    self._schedule_task(task)
                
            return True
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Importing schedule")
            return False

    def get_conflicts(self, start_time: datetime, 
                     duration: timedelta) -> List[Dict]:
        """Check for scheduling conflicts."""
        try:
            conflicts = []
            end_time = start_time + duration
            
            for task in self.scheduled_recordings.values():
                if not task.next_run:
                    continue
                    
                task_end = task.next_run + task.duration
                
                # Check for overlap
                if (start_time < task_end and 
                    end_time > task.next_run):
                    conflicts.append({
                        'id': task.id,
                        'name': task.name,
                        'start_time': task.next_run,
                        'duration': task.duration
                    })
            
            return conflicts
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Checking conflicts")
            return []

    def get_statistics(self) -> Dict:
        """Get recording schedule statistics."""
        try:
            now = datetime.now()
            total = len(self.scheduled_recordings)
            completed = sum(1 for task in self.scheduled_recordings.values()
                          if task.state == RecordingState.COMPLETED)
            failed = sum(1 for task in self.scheduled_recordings.values()
                        if task.state == RecordingState.FAILED)
            upcoming = sum(1 for task in self.scheduled_recordings.values()
                         if task.next_run and task.next_run > now)
            
            return {
                'total_recordings': total,
                'completed_recordings': completed,
                'failed_recordings': failed,
                'upcoming_recordings': upcoming,
                'active_timers': len(self.active_timers)
            }
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Getting statistics")
            return {}
    def cleanup(self):
        """Clean up resources."""
        try:
            self.stop()
            self.scheduled_recordings.clear()
            self.active_timers.clear()
            
        except Exception as e:
            self.error_handler.handle_error(e, context="Scheduler cleanup")