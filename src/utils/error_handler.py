# src/utils/error_handler.py
import logging
import traceback
import sys
from typing import Optional, Callable, Dict
from datetime import datetime
from pathlib import Path

class ErrorHandler:
    """Centralized error handling system."""
    
    def __init__(self, log_dir: str):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.error_callbacks: Dict[str, Callable] = {}
        self.setup_logging()
        self.install_global_handler()

    def setup_logging(self):
        """Configure logging system."""
        log_file = self.log_dir / f"error_{datetime.now():%Y%m%d}.log"
        
        # Configure root logger
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)

    def install_global_handler(self):
        """Install global exception handler."""
        def global_exception_handler(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                # Handle normal program termination
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return

            self.handle_error(exc_value, exc_traceback)

        sys.excepthook = global_exception_handler

    def handle_error(self, error: Exception, tb=None, 
                    context: str = None) -> bool:
        """Handle an error with logging and callbacks."""
        try:
            # Get error details
            error_type = type(error).__name__
            error_message = str(error)
            stack_trace = ''.join(traceback.format_tb(tb)) if tb else traceback.format_exc()
            
            # Log the error
            self.logger.error(
                f"Error in {context or 'unknown context'}: "
                f"{error_type}: {error_message}\n{stack_trace}"
            )
            
            # Call registered error callbacks
            for callback in self.error_callbacks.values():
                try:
                    callback(error_type, error_message, stack_trace, context)
                except Exception as e:
                    self.logger.error(f"Error in error callback: {e}")
            
            return True
            
        except Exception as e:
            # Fallback error handling
            print(f"Error in error handler: {e}")
            return False

    def register_callback(self, name: str, callback: Callable) -> bool:
        """Register an error callback."""
        try:
            self.error_callbacks[name] = callback
            return True
        except Exception as e:
            self.logger.error(f"Error registering callback: {e}")
            return False

    def unregister_callback(self, name: str) -> bool:
        """Unregister an error callback."""
        try:
            if name in self.error_callbacks:
                del self.error_callbacks[name]
            return True
        except Exception as e:
            self.logger.error(f"Error unregistering callback: {e}")
            return False

    def get_recent_errors(self, limit: int = 10) -> list:
        """Get recent errors from log file."""
        try:
            errors = []
            log_file = max(self.log_dir.glob("error_*.log"))
            
            with open(log_file, 'r') as f:
                lines = f.readlines()
                for line in reversed(lines):
                    if 'ERROR' in line:
                        errors.append(line.strip())
                        if len(errors) >= limit:
                            break
            
            return errors
            
        except Exception as e:
            self.logger.error(f"Error retrieving recent errors: {e}")
            return []