import logging
import os
from datetime import date
from logging.handlers import TimedRotatingFileHandler
from configuration import app_data

class ExcludeFilter(logging.Filter):
    """
    Filter that excludes specific log messages.
    In this case, messages containing 'aiohttp' are filtered out.
    """
    def filter(self, record: logging.LogRecord) -> bool:
        return "aiohttp" not in record.getMessage()

class EventTracker:
    """
    Custom logger class to handle various logging needs such as jobs, timers, errors, etc.
    Each logger has a separate file handler with time-based log rotation.
    """
    def __init__(self, log_level: int = logging.INFO):
        self.auditors = {}
        self.formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
        self.audit_path = app_data.audit_path
        
        # Prepare loggers for different purposes
        self.auditors['tasks'] = self._create_logger('tasks', log_level)
        self.auditors['pallet'] = self._create_logger('pallet', log_level)
        self.auditors['errors'] = self._create_logger('errors', log_level)
        self.auditors['linfosys'] = self._create_logger('linfosys', log_level)

    def _create_logger(self, name: str, log_level: int) -> logging.Logger:
        """
        Creates and configures a logger with a TimedRotatingFileHandler.
        Logs are rotated at midnight, creating a new file each day.
        """
        auditor = logging.getLogger(name)
        auditor.setLevel(log_level)

        # Create a file handler with daily log rotation
        log_file = os.path.join(self.audit_path, f'{name}.log')
        file_handler = TimedRotatingFileHandler(log_file, when="midnight")
        file_handler.setFormatter(self.formatter)
        
        # Attach the handler and a custom filter if needed
        auditor.addHandler(file_handler)
        auditor.addFilter(ExcludeFilter())

        return auditor

    def get_auditor(self, name: str) -> logging.Logger:
        """
        Returns the logger associated with the given name.
        """
        return self.auditors.get(name, self.auditors['tasks'])

# Initialize the logging system based on Settings configurations
event_tracker = EventTracker(app_data.audit_level)

# Access individual loggers
pallet_auditor = event_tracker.get_auditor('pallet')
tasks_auditor = event_tracker.get_auditor('tasks')
error_auditor = event_tracker.get_auditor('errors')
linfosys_auditor = event_tracker.get_auditor('linfosys')
