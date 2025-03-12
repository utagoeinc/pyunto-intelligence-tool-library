"""
Error detection and handling utility for Pyunto Intelligence API.

This module provides tools for detecting, analyzing, and responding to errors
in the Pyunto Intelligence API.
"""

import os
import time
import json
import logging
import threading
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, List, Optional, Union, Callable, Tuple, Any, Set
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("pyunto_error_detector.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("pyunto_error_detector")


class RecoveryStrategy(Enum):
    """Recovery strategies for API errors."""
    RETRY = "retry"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    CIRCUIT_BREAKER = "circuit_breaker"
    FALLBACK = "fallback"
    RETRY_WITH_FALLBACK = "retry_with_fallback"
    NOTIFY_ONLY = "notify_only"


class ErrorDetector:
    """
    Detects and responds to errors in the Pyunto Intelligence API.
    
    Features:
    - Error pattern detection
    - Automated recovery strategies
    - Error logging and analysis
    - Alerting for critical errors
    """
    
    def __init__(
        self,
        api_key: str,
        log_file: str = "error_log.jsonl",
        alert_email: Optional[str] = None,
        alert_webhook: Optional[str] = None,
        max_errors_to_track: int = 1000
    ):
        """
        Initialize the error detector.
        
        Args:
            api_key: Pyunto Intelligence API key
            log_file: File to store error logs
            alert_email: Email address for alerts (optional)
            alert_webhook: Webhook URL for alerts (optional)
            max_errors_to_track: Maximum number of errors to keep in memory
        """
        self.api_key = api_key
        self.log_file = log_file
        self.alert_email = alert_email
        self.alert_webhook = alert_webhook
        
        # Error tracking
        self.errors = deque(maxlen=max_errors_to_track)
        self.error_counts = defaultdict(int)  # Count by error code
        self.error_patterns = defaultdict(list)  # Patterns by endpoint
        
        # Recovery strategies
        self.recovery_strategies = {}  # Strategies by error code
        
        # Circuit breaker state
        self.circuit_breaker = {
            "is_open": False,
            "failure_count": 0,
            "last_failure_time": None,
            "reset_timeout": 60  # seconds
        }
        
        # Detection state
        self.detection_active = False
        self.detector_thread = None
        
        # Constants
        self.CIRCUIT_BREAKER_THRESHOLD = 5  # failures
        self.MAX_RETRIES = 3
        self.RETRY_BASE_DELAY = 1  # seconds
        
        # Load existing error logs if available
        self._load_error_logs()
    
    def add_recovery_strategy(
        self,
        error_code: Union[int, str],
        strategy: RecoveryStrategy,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
        fallback_endpoint: Optional[str] = None
    ):
        """
        Add a recovery strategy for a specific error code.
        
        Args:
            error_code: HTTP status code or error string
            strategy: Recovery strategy to use
            max_retries: Maximum number of retries
            backoff_factor: Factor for exponential backoff
            fallback_endpoint: Alternative endpoint for fallback strategy
        """
        self.recovery_strategies[str(error_code)] = {
            "strategy": strategy,
            "max_retries": max_retries,
            "backoff_factor": backoff_factor,
            "fallback_endpoint": fallback_endpoint
        }
        
        logger.info(f"Added {strategy.value} recovery strategy for error code {error_code}")
    
    def start(self):
        """Start the error detection process."""
        if self.detection_active:
            logger.warning("Error detection is already active")
            return
        
        self.detection_active = True
        self.detector_thread = threading.Thread(target=self._detection_loop)
        self.detector_thread.daemon = True
        self.detector_thread.start()
        
        logger.info("Pyunto Intelligence error detection started")
    
    def stop(self):
        """Stop the error detection process."""
        if not self.detection_active:
            logger.warning("Error detection is not active")
            return
        
        self.detection_active = False
        if self.detector_thread:
            self.detector_thread.join(timeout=60)
        
        logger.info("Pyunto Intelligence error detection stopped")
    
    def track_error(
        self,
        error_code: Union[int, str],
        error_message: str,
        endpoint: str,
        request_data: Optional[Dict] = None,
        response_data: Optional[Dict] = None
    ):
        """
        Track an API error manually.
        
        Args:
            error_code: HTTP status code or error string
            error_message: Error message
            endpoint: API endpoint that was called
            request_data: Optional request data for context
            response_data: Optional response data for context
        """
        timestamp = datetime.now()
        error_code = str(error_code)
        
        # Create error entry
        error_entry = {
            "timestamp": timestamp.isoformat(),
            "error_code": error_code,
            "error_message": error_message,
            "endpoint": endpoint,
            "request_data": request_data,
            "response_data": response_data
        }
        
        # Add to tracking structures
        self.errors.append(error_entry)
        self.error_counts[error_code] += 1
        
        # Add to pattern tracking
        pattern_key = f"{endpoint}:{error_code}"
        self.error_patterns[pattern_key].append(timestamp)
        
        # Clean up old pattern entries (older than 24 hours)
        cutoff_time = timestamp - timedelta(hours=24)
        self.error_patterns[pattern_key] = [
            t for t in self.error_patterns[pattern_key]
            if datetime.fromisoformat(t.isoformat()) > cutoff_time
        ]
        
        # Log the error
        self._log_error(error_entry)
        
        # Check for patterns
        self._analyze_patterns(pattern_key, endpoint, error_code)
        
        # Apply recovery strategy if configured
        if error_code in self.recovery_strategies:
            self._apply_recovery_strategy(
                error_code, 
                endpoint,
                request_data,
                error_entry
            )
        
        logger.debug(f"Tracked error {error_code} on {endpoint}: {error_message}")
    
    def get_error_summary(self) -> Dict[str, Any]:
        """
        Get a summary of recent errors.
        
        Returns:
            Dict containing error metrics
        """
        now = datetime.now()
        
        # Count errors in the last hour
        hour_ago = now - timedelta(hours=1)
        errors_last_hour = sum(
            1 for error in self.errors
            if datetime.fromisoformat(error["timestamp"]) > hour_ago
        )
        
        # Count errors in the last day
        day_ago = now - timedelta(days=1)
        errors_last_day = sum(
            1 for error in self.errors
            if datetime.fromisoformat(error["timestamp"]) > day_ago
        )
        
        # Most common error codes
        top_error_codes = sorted(
            self.error_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        # Most common endpoints with errors
        endpoint_errors = defaultdict(int)
        for error in self.errors:
            endpoint_errors[error["endpoint"]] += 1
        
        top_endpoints = sorted(
            endpoint_errors.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        # Circuit breaker status
        circuit_breaker_status = "open" if self.circuit_breaker["is_open"] else "closed"
        
        return {
            "total_errors_tracked": len(self.errors),
            "errors_last_hour": errors_last_hour,
            "errors_last_day": errors_last_day,
            "top_error_codes": dict(top_error_codes),
            "top_error_endpoints": dict(top_endpoints),
            "circuit_breaker_status": circuit_breaker_status,
            "circuit_breaker_failure_count": self.circuit_breaker["failure_count"],
            "recovery_strategies_configured": len(self.recovery_strategies),
            "timestamp": now.isoformat()
        }
    
    def search_errors(
        self,
        error_code: Optional[str] = None,
        endpoint: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Search for specific errors.
        
        Args:
            error_code: Filter by error code
            endpoint: Filter by endpoint
            start_time: Filter by start time
            end_time: Filter by end time
            limit: Maximum number of results
            
        Returns:
            List of matching error entries
        """
        results = []
        
        for error in self.errors:
            # Apply filters
            if error_code and error["error_code"] != error_code:
                continue
            
            if endpoint and error["endpoint"] != endpoint:
                continue
            
            error_time = datetime.fromisoformat(error["timestamp"])
            
            if start_time and error_time < start_time:
                continue
                
            if end_time and error_time > end_time:
                continue
            
            results.append(error)
            
            if len(results) >= limit:
                break
        
        return results
    
    def reset_circuit_breaker(self):
        """Manually reset the circuit breaker."""
        self.circuit_breaker["is_open"] = False
        self.circuit_breaker["failure_count"] = 0
        self.circuit_breaker["last_failure_time"] = None
        
        logger.info("Circuit breaker manually reset")
    
    def _detection_loop(self):
        """Internal detection loop that runs periodically."""
        while self.detection_active:
            try:
                # Check circuit breaker status
                self._check_circuit_breaker()
                
                # Check for recurring patterns
                self._check_recurring_patterns()
                
                # Generate periodic report (daily)
                current_hour = datetime.now().hour
                if current_hour == 0:  # Midnight
                    self._generate_daily_report()
                
            except Exception as e:
                logger.error(f"Error in detection loop: {e}")
            
            # Sleep briefly
            time.sleep(60)  # Check every minute
    
    def _check_circuit_breaker(self):
        """Check if the circuit breaker should be reset."""
        if not self.circuit_breaker["is_open"]:
            return
        
        now = datetime.now()
        last_failure = self.circuit_breaker["last_failure_time"]
        
        if last_failure and (now - last_failure).total_seconds() > self.circuit_breaker["reset_timeout"]:
            # Reset the circuit breaker after timeout
            self.reset_circuit_breaker()
            logger.info("Circuit breaker automatically reset after timeout")
    
    def _check_recurring_patterns(self):
        """Check for recurring error patterns."""
        now = datetime.now()
        
        for pattern_key, timestamps in self.error_patterns.items():
            if len(timestamps) < 5:
                continue
            
            # Only consider timestamps in the last hour
            recent_timestamps = [
                t for t in timestamps
                if (now - t).total_seconds() < 3600
            ]
            
            if len(recent_timestamps) >= 5:
                # We have a recurring pattern (5+ errors of the same type in the last hour)
                endpoint, error_code = pattern_key.split(':')
                
                # Alert about the pattern
                self._send_alert(
                    alert_type="Recurring Error Pattern",
                    message=f"Detected recurring error pattern: {error_code} on {endpoint} ({len(recent_timestamps)} occurrences in the last hour)",
                    details={
                        "pattern_key": pattern_key,
                        "error_code": error_code,
                        "endpoint": endpoint,
                        "occurrences": len(recent_timestamps),
                        "first_occurrence": min(recent_timestamps).isoformat(),
                        "last_occurrence": max(recent_timestamps).isoformat()
                    }
                )
                
                logger.warning(f"Recurring error pattern detected: {error_code} on {endpoint}")
    
    def _analyze_patterns(self, pattern_key: str, endpoint: str, error_code: str):
        """Analyze error patterns for a specific endpoint and error code."""
        timestamps = self.error_patterns[pattern_key]
        
        if len(timestamps) < 3:
            return
        
        # Calculate time between errors
        intervals = []
        for i in range(1, len(timestamps)):
            delta = (timestamps[i] - timestamps[i-1]).total_seconds()
            intervals.append(delta)
        
        # Check for very frequent errors (less than 10 seconds apart)
        recent_intervals = intervals[-2:]  # Last 2 intervals
        if all(interval < 10 for interval in recent_intervals):
            # This might be a severe issue, alert immediately
            self._send_alert(
                alert_type="Rapid Error Sequence",
                message=f"Detected rapid error sequence: {error_code} on {endpoint} (multiple errors within seconds)",
                details={
                    "pattern_key": pattern_key,
                    "error_code": error_code,
                    "endpoint": endpoint,
                    "recent_intervals": recent_intervals,
                    "total_occurrences": len(timestamps)
                }
            )
            
            logger.warning(f"Rapid error sequence detected: {error_code} on {endpoint}")
            
            # Consider opening the circuit breaker
            self._increment_circuit_breaker()
    
    def _apply_recovery_strategy(
        self,
        error_code: str,
        endpoint: str,
        request_data: Optional[Dict],
        error_entry: Dict
    ):
        """Apply the configured recovery strategy for an error."""
        if self.circuit_breaker["is_open"]:
            logger.warning("Circuit breaker is open, skipping recovery strategy")
            return
        
        strategy_config = self.recovery_strategies[error_code]
        strategy_type = RecoveryStrategy(strategy_config["strategy"]) if isinstance(strategy_config["strategy"], str) else strategy_config["strategy"]
        
        if strategy_type == RecoveryStrategy.RETRY:
            self._apply_retry_strategy(
                endpoint, 
                request_data, 
                strategy_config["max_retries"]
            )
            
        elif strategy_type == RecoveryStrategy.EXPONENTIAL_BACKOFF:
            self._apply_backoff_strategy(
                endpoint, 
                request_data, 
                strategy_config["max_retries"],
                strategy_config["backoff_factor"]
            )
            
        elif strategy_type == RecoveryStrategy.CIRCUIT_BREAKER:
            self._increment_circuit_breaker()
            
        elif strategy_type == RecoveryStrategy.FALLBACK:
            self._apply_fallback_strategy(
                endpoint, 
                request_data, 
                strategy_config["fallback_endpoint"]
            )
            
        elif strategy_type == RecoveryStrategy.RETRY_WITH_FALLBACK:
            success = self._apply_retry_strategy(
                endpoint, 
                request_data, 
                strategy_config["max_retries"]
            )
            
            if not success and strategy_config["fallback_endpoint"]:
                self._apply_fallback_strategy(
                    endpoint, 
                    request_data, 
                    strategy_config["fallback_endpoint"]
                )
                
        elif strategy_type == RecoveryStrategy.NOTIFY_ONLY:
            self._send_alert(
                alert_type=f"Error {error_code}",
                message=f"Error detected: {error_code} on {endpoint}",
                details=error_entry
            )
    
    def _apply_retry_strategy(
        self,
        endpoint: str,
        request_data: Optional[Dict],
        max_retries: int
    ) -> bool:
        """
        Apply a simple retry strategy.
        
        Returns:
            bool: True if retry succeeded, False otherwise
        """
        if not request_data:
            logger.warning("Cannot retry without request data")
            return False
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Retry attempt {attempt + 1}/{max_retries} for {endpoint}")
                
                # Simple delay between retries (1 second)
                time.sleep(1)
                
                # Make the request
                response = requests.post(
                    endpoint,
                    json=request_data,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    timeout=30
                )
                
                # Check if successful
                if 200 <= response.status_code < 300:
                    logger.info(f"Retry succeeded on attempt {attempt + 1}")
                    return True
                
            except Exception as e:
                logger.warning(f"Retry attempt {attempt + 1} failed: {str(e)}")
        
        logger.warning(f"All {max_retries} retry attempts failed")
        return False
    
    def _apply_backoff_strategy(
        self,
        endpoint: str,
        request_data: Optional[Dict],
        max_retries: int,
        backoff_factor: float
    ) -> bool:
        """
        Apply an exponential backoff retry strategy.
        
        Returns:
            bool: True if retry succeeded, False otherwise
        """
        if not request_data:
            logger.warning("Cannot retry without request data")
            return False
        
        for attempt in range(max_retries):
            try:
                # Calculate backoff delay
                delay = self.RETRY_BASE_DELAY * (backoff_factor ** attempt)
                logger.info(f"Backoff retry attempt {attempt + 1}/{max_retries} for {endpoint} (delay: {delay:.2f}s)")
                
                # Apply backoff delay
                time.sleep(delay)
                
                # Make the request
                response = requests.post(
                    endpoint,
                    json=request_data,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    timeout=30
                )
                
                # Check if successful
                if 200 <= response.status_code < 300:
                    logger.info(f"Backoff retry succeeded on attempt {attempt + 1}")
                    return True
                
            except Exception as e:
                logger.warning(f"Backoff retry attempt {attempt + 1} failed: {str(e)}")
        
        logger.warning(f"All {max_retries} backoff retry attempts failed")
        return False
    
    def _apply_fallback_strategy(
        self,
        endpoint: str,
        request_data: Optional[Dict],
        fallback_endpoint: Optional[str]
    ) -> bool:
        """
        Apply a fallback strategy.
        
        Returns:
            bool: True if fallback succeeded, False otherwise
        """
        if not request_data or not fallback_endpoint:
            logger.warning("Cannot use fallback without request data or fallback endpoint")
            return False
        
        try:
            logger.info(f"Attempting fallback to {fallback_endpoint}")
            
            # Make the fallback request
            response = requests.post(
                fallback_endpoint,
                json=request_data,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                timeout=30
            )
            
            # Check if successful
            if 200 <= response.status_code < 300:
                logger.info("Fallback succeeded")
                return True
            else:
                logger.warning(f"Fallback failed with status {response.status_code}")
                return False
            
        except Exception as e:
            logger.warning(f"Fallback request failed: {str(e)}")
            return False
    
    def _increment_circuit_breaker(self):
        """Increment the circuit breaker failure count and potentially open it."""
        self.circuit_breaker["failure_count"] += 1
        self.circuit_breaker["last_failure_time"] = datetime.now()
        
        if self.circuit_breaker["failure_count"] >= self.CIRCUIT_BREAKER_THRESHOLD:
            # Open the circuit breaker
            if not self.circuit_breaker["is_open"]:
                self.circuit_breaker["is_open"] = True
                logger.warning(f"Circuit breaker opened after {self.circuit_breaker['failure_count']} failures")
                
                # Send alert
                self._send_alert(
                    alert_type="Circuit Breaker Opened",
                    message=f"Circuit breaker opened after {self.circuit_breaker['failure_count']} failures",
                    details={
                        "failure_count": self.circuit_breaker["failure_count"],
                        "threshold": self.CIRCUIT_BREAKER_THRESHOLD,
                        "reset_timeout": self.circuit_breaker["reset_timeout"]
                    }
                )
    
    def _log_error(self, error_entry: Dict):
        """Log an error to the error log file."""
        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(error_entry) + "\n")
        except Exception as e:
            logger.error(f"Failed to log error: {str(e)}")
    
    def _load_error_logs(self):
        """Load error logs from file if it exists."""
        if not os.path.exists(self.log_file):
            logger.info(f"No error log file found at {self.log_file}")
            return
        
        try:
            with open(self.log_file, "r") as f:
                for line in f:
                    try:
                        error = json.loads(line.strip())
                        
                        # Add to tracking structures
                        self.errors.append(error)
                        self.error_counts[error["error_code"]] += 1
                        
                        # Add to pattern tracking
                        pattern_key = f"{error['endpoint']}:{error['error_code']}"
                        timestamp = datetime.fromisoformat(error["timestamp"])
                        
                        # Only add recent errors to patterns (last 24 hours)
                        if (datetime.now() - timestamp).total_seconds() < 86400:  # 24 hours
                            self.error_patterns[pattern_key].append(timestamp)
                        
                    except Exception as e:
                        logger.warning(f"Failed to parse error log line: {str(e)}")
            
            logger.info(f"Loaded {len(self.errors)} errors from {self.log_file}")
            
        except Exception as e:
            logger.error(f"Failed to load error logs: {str(e)}")
    
    def _generate_daily_report(self):
        """Generate and send a daily error report."""
        summary = self.get_error_summary()
        
        # Generate report text
        report = f"""
        Pyunto Intelligence Daily Error Report
        Date: {datetime.now().strftime("%Y-%m-%d")}
        
        Error Summary:
        - Total errors tracked: {summary['total_errors_tracked']}
        - Errors in the last 24 hours: {summary['errors_last_day']}
        - Circuit breaker status: {summary['circuit_breaker_status']}
        
        Top Error Codes:
        {json.dumps(summary['top_error_codes'], indent=2)}
        
        Top Error Endpoints:
        {json.dumps(summary['top_error_endpoints'], indent=2)}
        
        This is an automated report from the Pyunto Intelligence error detection system.
        """
        
        # Send report
        self._send_alert(
            alert_type="Daily Error Report",
            message=report,
            details=summary
        )
        
        logger.info("Daily error report generated and sent")
    
    def _send_alert(self, alert_type: str, message: str, details: Optional[Dict] = None):
        """Send an alert via configured channels."""
        if self.alert_email:
            subject = f"Pyunto Intelligence Alert: {alert_type}"
            self._send_email(subject, message)
        
        if self.alert_webhook:
            self._send_webhook(alert_type, message, details)
    
    def _send_email(self, subject: str, body: str):
        """Send an email alert."""
        if not self.alert_email:
            return
        
        # Check if SMTP settings are configured
        smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        smtp_user = os.environ.get("SMTP_USER")
        smtp_pass = os.environ.get("SMTP_PASS")
        
        if not smtp_user or not smtp_pass:
            logger.warning("SMTP credentials not configured, cannot send email alert")
            return
        
        # Create message
        message = MIMEMultipart()
        message["From"] = smtp_user
        message["To"] = self.alert_email
        message["Subject"] = subject
        
        # Attach body
        message.attach(MIMEText(body, "plain"))
        
        try:
            # Connect to SMTP server
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_pass)
            
            # Send email
            server.sendmail(smtp_user, self.alert_email, message.as_string())
            server.quit()
            
            logger.info(f"Alert email sent to {self.alert_email}")
            
        except Exception as e:
            logger.error(f"Failed to send alert email: {e}")
    
    def _send_webhook(self, alert_type: str, message: str, details: Optional[Dict] = None):
        """Send an alert to a webhook."""
        if not self.alert_webhook:
            return
        
        payload = {
            "type": alert_type,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "service": "PyuntoErrorDetector"
        }
        
        if details:
            payload["details"] = details
        
        try:
            response = requests.post(
                self.alert_webhook,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code < 200 or response.status_code >= 300:
                logger.warning(f"Webhook returned non-success status: {response.status_code}")
            else:
                logger.info("Alert webhook notification sent")
                
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get detailed statistics about error patterns and recovery.
        
        Returns:
            Dict containing comprehensive error statistics
        """
        stats = {
            "error_counts": dict(self.error_counts),
            "circuit_breaker": {
                "is_open": self.circuit_breaker["is_open"],
                "failure_count": self.circuit_breaker["failure_count"],
                "reset_timeout": self.circuit_breaker["reset_timeout"],
                "last_failure": self.circuit_breaker["last_failure_time"].isoformat() 
                    if self.circuit_breaker["last_failure_time"] else None
            },
            "recovery_strategies": {
                code: {
                    "strategy": strategy["strategy"].value 
                        if isinstance(strategy["strategy"], RecoveryStrategy) else strategy["strategy"],
                    "max_retries": strategy["max_retries"],
                    "backoff_factor": strategy.get("backoff_factor"),
                    "fallback_endpoint": strategy.get("fallback_endpoint")
                }
                for code, strategy in self.recovery_strategies.items()
            },
            "error_patterns": {
                pattern_key: {
                    "count": len(timestamps),
                    "first_seen": min(timestamps).isoformat() if timestamps else None,
                    "last_seen": max(timestamps).isoformat() if timestamps else None,
                    "frequency_per_hour": len([t for t in timestamps 
                                             if (datetime.now() - t).total_seconds() < 3600])
                }
                for pattern_key, timestamps in self.error_patterns.items()
            }
        }
        
        return stats
    
    def export_config(self, file_path: str) -> bool:
        """
        Export error detector configuration to a JSON file.
        
        Args:
            file_path: Path to save the configuration file
            
        Returns:
            bool: True if successful, False otherwise
        """
        config = {
            "log_file": self.log_file,
            "alert_email": self.alert_email,
            "alert_webhook": self.alert_webhook,
            "circuit_breaker_threshold": self.CIRCUIT_BREAKER_THRESHOLD,
            "circuit_breaker_reset_timeout": self.circuit_breaker["reset_timeout"],
            "max_retries": self.MAX_RETRIES,
            "retry_base_delay": self.RETRY_BASE_DELAY,
            "recovery_strategies": {
                code: {
                    "strategy": strategy["strategy"].value 
                        if isinstance(strategy["strategy"], RecoveryStrategy) else strategy["strategy"],
                    "max_retries": strategy["max_retries"],
                    "backoff_factor": strategy.get("backoff_factor"),
                    "fallback_endpoint": strategy.get("fallback_endpoint")
                }
                for code, strategy in self.recovery_strategies.items()
            }
        }
        
        try:
            with open(file_path, "w") as f:
                json.dump(config, f, indent=2)
            
            logger.info(f"Exported configuration to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export configuration: {e}")
            return False
    
    def import_config(self, file_path: str) -> bool:
        """
        Import error detector configuration from a JSON file.
        
        Args:
            file_path: Path to the configuration file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(file_path, "r") as f:
                config = json.load(f)
            
            # Apply configuration
            if "log_file" in config:
                self.log_file = config["log_file"]
            
            if "alert_email" in config:
                self.alert_email = config["alert_email"]
                
            if "alert_webhook" in config:
                self.alert_webhook = config["alert_webhook"]
                
            if "circuit_breaker_threshold" in config:
                self.CIRCUIT_BREAKER_THRESHOLD = config["circuit_breaker_threshold"]
                
            if "circuit_breaker_reset_timeout" in config:
                self.circuit_breaker["reset_timeout"] = config["circuit_breaker_reset_timeout"]
                
            if "max_retries" in config:
                self.MAX_RETRIES = config["max_retries"]
                
            if "retry_base_delay" in config:
                self.RETRY_BASE_DELAY = config["retry_base_delay"]
                
            # Import recovery strategies
            if "recovery_strategies" in config:
                for code, strategy_config in config["recovery_strategies"].items():
                    try:
                        strategy = RecoveryStrategy(strategy_config["strategy"])
                        self.add_recovery_strategy(
                            error_code=code,
                            strategy=strategy,
                            max_retries=strategy_config.get("max_retries", 3),
                            backoff_factor=strategy_config.get("backoff_factor", 2.0),
                            fallback_endpoint=strategy_config.get("fallback_endpoint")
                        )
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Failed to import recovery strategy for code {code}: {e}")
            
            logger.info(f"Imported configuration from {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to import configuration: {e}")
            return False
            
    def add_custom_alert_handler(self, handler: Callable[[str, str, Optional[Dict]], None]):
        """
        Add a custom alert handler function.
        
        Args:
            handler: Function that takes alert_type, message, and optional details
        """
        self._custom_alert_handler = handler
        logger.info("Custom alert handler added")
        
    def get_error_rates(self, interval_minutes: int = 60) -> Dict[str, Any]:
        """
        Calculate error rates over a specified time interval.
        
        Args:
            interval_minutes: Time interval in minutes
            
        Returns:
            Dict containing error rates and trends
        """
        now = datetime.now()
        interval_start = now - timedelta(minutes=interval_minutes)
        
        # Filter recent errors
        recent_errors = [
            error for error in self.errors
            if datetime.fromisoformat(error["timestamp"]) > interval_start
        ]
        
        # Count errors by code
        error_counts = defaultdict(int)
        for error in recent_errors:
            error_counts[error["error_code"]] += 1
            
        # Calculate rates (errors per minute)
        error_rates = {
            code: count / interval_minutes
            for code, count in error_counts.items()
        }
        
        # Calculate trends (comparing to previous interval)
        previous_start = interval_start - timedelta(minutes=interval_minutes)
        previous_errors = [
            error for error in self.errors
            if previous_start < datetime.fromisoformat(error["timestamp"]) <= interval_start
        ]
        
        previous_counts = defaultdict(int)
        for error in previous_errors:
            previous_counts[error["error_code"]] += 1
            
        trends = {}
        for code in set(list(error_counts.keys()) + list(previous_counts.keys())):
            current = error_counts[code]
            previous = previous_counts[code]
            
            if previous == 0:
                if current == 0:
                    trend = 0  # No change
                else:
                    trend = 100  # New error type
            else:
                trend = ((current - previous) / previous) * 100  # Percentage change
                
            trends[code] = {
                "current_count": current,
                "previous_count": previous,
                "percent_change": round(trend, 2)
            }
        
        return {
            "interval_minutes": interval_minutes,
            "total_errors": len(recent_errors),
            "error_rates": error_rates,
            "trends": trends,
            "timestamp": now.isoformat()
        }


# Example usage
if __name__ == "__main__":
    # Get API key from environment
    api_key = os.environ.get("PYUNTO_API_KEY")
    
    if not api_key:
        logger.error("No API key found. Set PYUNTO_API_KEY environment variable.")
        exit(1)
    
    # Initialize error detector
    detector = ErrorDetector(
        api_key=api_key,
        alert_email=os.environ.get("ALERT_EMAIL"),
        alert_webhook=os.environ.get("ALERT_WEBHOOK", "https://hooks.slack.com/services/your/webhook/url")
    )
    
    # Configure recovery strategies
    detector.add_recovery_strategy(
        error_code=429,  # Rate limiting
        strategy=RecoveryStrategy.EXPONENTIAL_BACKOFF,
        max_retries=5,
        backoff_factor=2.0
    )
    
    detector.add_recovery_strategy(
        error_code=500,  # Server error
        strategy=RecoveryStrategy.RETRY_WITH_FALLBACK,
        max_retries=3,
        fallback_endpoint="https://a.pyunto.com/api/i/v1/fallback"
    )
    
    detector.add_recovery_strategy(
        error_code=503,  # Service unavailable
        strategy=RecoveryStrategy.CIRCUIT_BREAKER
    )
    
    # Start error detection
    detector.start()
    
    try:
        # Simulate some errors for testing
        for i in range(3):
            # Rate limiting error
            detector.track_error(
                error_code=429,
                error_message="Too Many Requests",
                endpoint="https://a.pyunto.com/api/i/v1",
                request_data={"type": "image", "data": "base64_encoded_data"}
            )
            
            # Server error
            detector.track_error(
                error_code=500,
                error_message="Internal Server Error",
                endpoint="https://a.pyunto.com/api/i/v1/analyze",
                request_data={"assistantId": "asst_123", "type": "text"}
            )
            
            time.sleep(1)
        
        # Get error summary
        summary = detector.get_error_summary()
        logger.info(f"Error summary: {json.dumps(summary, indent=2)}")
        
        # Search for specific errors
        rate_limit_errors = detector.search_errors(error_code="429")
        logger.info(f"Found {len(rate_limit_errors)} rate limit errors")
        
        # Wait for detection loop to run
        logger.info("Press Ctrl+C to stop...")
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Stopping error detection...")
        detector.stop()
        logger.info("Error detection stopped.")
