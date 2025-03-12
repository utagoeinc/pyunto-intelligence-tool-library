"""
Performance monitoring utility for Pyunto Intelligence API.

This module provides tools for monitoring the performance of the Pyunto Intelligence API,
including response times, success rates, and usage patterns.
"""

import os
import time
import json
import logging
import threading
import statistics
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from collections import deque, defaultdict
import matplotlib.pyplot as plt
from typing import Dict, List, Optional, Union, Callable, Tuple, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("pyunto_monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("pyunto_monitor")

class PyuntoMonitor:
    """Pyunto Intelligence API performance monitor."""
    
    def __init__(
        self,
        api_key: str,
        api_url: str = "https://a.pyunto.com/api/i/v1",
        alert_email: Optional[str] = None,
        alert_webhook: Optional[str] = None,
        metrics_file: str = "pyunto_metrics.jsonl",
        enable_visualization: bool = True
    ):
        """
        Initialize the monitor.
        
        Args:
            api_key: Pyunto Intelligence API key
            api_url: Base URL for the API
            alert_email: Email address for alerts (optional)
            alert_webhook: Webhook URL for alerts (optional)
            metrics_file: File to store metrics data
            enable_visualization: Whether to enable visualization features
        """
        self.api_key = api_key
        self.api_url = api_url
        self.alert_email = alert_email
        self.alert_webhook = alert_webhook
        self.metrics_file = metrics_file
        self.enable_visualization = enable_visualization
        
        # Performance metrics
        self.response_times = deque(maxlen=1000)  # Last 1000 response times
        self.error_rates = deque(maxlen=100)  # Last 100 error rate measurements
        self.usage_by_hour = defaultdict(int)  # Usage count by hour
        self.usage_by_day = defaultdict(int)  # Usage count by day
        self.status_codes = defaultdict(int)  # Count of status codes
        
        # Alert thresholds
        self.response_time_threshold_ms = 2000  # Default: 2 seconds
        self.error_rate_threshold = 0.1  # Default: 10%
        self.quota_warning_threshold = 0.8  # Default: 80% of quota
        
        # Monitoring state
        self.monitoring_active = False
        self.monitor_thread = None
        self.check_interval_seconds = 300  # Default: check every 5 minutes
        
        # Load existing metrics if available
        self._load_metrics()
        
        # Last alert timestamps to prevent alert storms
        self.last_alerts = {
            "response_time": datetime.min,
            "error_rate": datetime.min,
            "quota": datetime.min
        }
        
        # Alert cooldown period (in hours)
        self.alert_cooldown_hours = 2
    
    def setup_basic_monitoring(
        self,
        check_interval_seconds: int = 300,
        response_time_threshold_ms: int = 2000,
        error_rate_threshold: float = 0.1,
        quota_warning_threshold: float = 0.8
    ):
        """
        Set up basic monitoring with specified thresholds.
        
        Args:
            check_interval_seconds: How often to check metrics (in seconds)
            response_time_threshold_ms: Alert threshold for response time (ms)
            error_rate_threshold: Alert threshold for error rate (0.0-1.0)
            quota_warning_threshold: Alert threshold for quota usage (0.0-1.0)
        """
        self.check_interval_seconds = check_interval_seconds
        self.response_time_threshold_ms = response_time_threshold_ms
        self.error_rate_threshold = error_rate_threshold
        self.quota_warning_threshold = quota_warning_threshold
        
        logger.info(f"Basic monitoring set up with: "
                   f"check_interval={check_interval_seconds}s, "
                   f"response_time_threshold={response_time_threshold_ms}ms, "
                   f"error_rate_threshold={error_rate_threshold*100}%, "
                   f"quota_warning_threshold={quota_warning_threshold*100}%")
    
    def start(self):
        """Start the monitoring process."""
        if self.monitoring_active:
            logger.warning("Monitoring is already active")
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        logger.info("Pyunto Intelligence monitoring started")
    
    def stop(self):
        """Stop the monitoring process."""
        if not self.monitoring_active:
            logger.warning("Monitoring is not active")
            return
        
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=60)
        
        # Save metrics before stopping
        self._save_metrics()
        
        logger.info("Pyunto Intelligence monitoring stopped")
    
    def track_request(
        self,
        endpoint: str,
        response_time_ms: float,
        status_code: int,
        request_data: Optional[Dict] = None
    ):
        """
        Track a single API request manually.
        
        Args:
            endpoint: API endpoint that was called
            response_time_ms: Response time in milliseconds
            status_code: HTTP status code
            request_data: Optional request data for context
        """
        timestamp = datetime.now()
        
        # Record response time
        self.response_times.append(response_time_ms)
        
        # Record status code
        self.status_codes[status_code] += 1
        
        # Record usage by time
        hour_key = timestamp.strftime("%Y-%m-%d %H:00")
        day_key = timestamp.strftime("%Y-%m-%d")
        self.usage_by_hour[hour_key] += 1
        self.usage_by_day[day_key] += 1
        
        # Calculate current error rate (last 100 requests)
        total_requests = sum(self.status_codes.values())
        error_requests = sum(self.status_codes.get(code, 0) for code in range(400, 600))
        
        if total_requests > 0:
            current_error_rate = error_requests / total_requests
            self.error_rates.append(current_error_rate)
        
        # Check for concerning metrics
        self._check_alerts(response_time_ms, current_error_rate, endpoint)
        
        # Save metrics periodically (every 100 requests)
        if total_requests % 100 == 0:
            self._save_metrics()
        
        logger.debug(f"Tracked request to {endpoint}: {status_code}, {response_time_ms}ms")
    
    def health_check(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Perform a health check of the Pyunto Intelligence API.
        
        Returns:
            Tuple of (is_healthy, metrics)
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            # Make a simple health check request
            start_time = time.time()
            response = requests.get(
                f"{self.api_url}/health",
                headers=headers,
                timeout=10
            )
            end_time = time.time()
            
            response_time_ms = (end_time - start_time) * 1000
            is_success = 200 <= response.status_code < 300
            
            # Track this request
            self.track_request(
                endpoint="/health",
                response_time_ms=response_time_ms,
                status_code=response.status_code
            )
            
            # Get quota information if available
            quota_info = {}
            try:
                quota_response = requests.get(
                    f"{self.api_url}/quota",
                    headers=headers,
                    timeout=10
                )
                if quota_response.status_code == 200:
                    quota_info = quota_response.json()
            except Exception as e:
                logger.warning(f"Failed to get quota information: {e}")
            
            metrics = {
                "is_healthy": is_success,
                "response_time_ms": response_time_ms,
                "status_code": response.status_code,
                "timestamp": datetime.now().isoformat(),
                "quota_info": quota_info
            }
            
            return is_success, metrics
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            
            # Track as a failed request
            self.track_request(
                endpoint="/health",
                response_time_ms=10000,  # 10 seconds as a default for failed requests
                status_code=500  # Use 500 as a default for exceptions
            )
            
            metrics = {
                "is_healthy": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            
            return False, metrics
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current performance metrics.
        
        Returns:
            Dict containing performance metrics
        """
        # Calculate response time statistics
        response_times = list(self.response_times)
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            median_response_time = statistics.median(response_times)
            p95_response_time = sorted(response_times)[int(len(response_times) * 0.95)]
        else:
            avg_response_time = median_response_time = p95_response_time = 0
        
        # Calculate error rate
        total_requests = sum(self.status_codes.values())
        error_requests = sum(self.status_codes.get(code, 0) for code in range(400, 600))
        
        if total_requests > 0:
            current_error_rate = error_requests / total_requests
        else:
            current_error_rate = 0
        
        # Get recent usage
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        
        today_usage = self.usage_by_day.get(today, 0)
        yesterday_usage = self.usage_by_day.get(yesterday, 0)
        
        return {
            "response_time": {
                "average_ms": round(avg_response_time, 2),
                "median_ms": round(median_response_time, 2),
                "p95_ms": round(p95_response_time, 2),
                "samples": len(response_times)
            },
            "error_rate": {
                "current": round(current_error_rate * 100, 2),
                "total_requests": total_requests,
                "error_requests": error_requests
            },
            "usage": {
                "today": today_usage,
                "yesterday": yesterday_usage,
                "last_7_days": sum(
                    self.usage_by_day.get(
                        (now - timedelta(days=i)).strftime("%Y-%m-%d"), 
                        0
                    ) for i in range(7)
                )
            },
            "status_codes": dict(self.status_codes),
            "timestamp": datetime.now().isoformat()
        }
    
    def visualize_metrics(self, output_dir: str = "reports"):
        """
        Generate visualizations of the metrics.
        
        Args:
            output_dir: Directory to save the visualizations
        """
        if not self.enable_visualization:
            logger.warning("Visualization is disabled")
            return
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Response time over time
        if self.response_times:
            plt.figure(figsize=(12, 6))
            plt.plot(list(self.response_times))
            plt.title("Response Time (ms)")
            plt.xlabel("Request #")
            plt.ylabel("Response Time (ms)")
            plt.axhline(y=self.response_time_threshold_ms, color='r', linestyle='--')
            plt.grid(True)
            plt.savefig(os.path.join(output_dir, "response_times.png"))
            plt.close()
        
        # Error rate over time
        if self.error_rates:
            plt.figure(figsize=(12, 6))
            plt.plot([rate * 100 for rate in self.error_rates])
            plt.title("Error Rate (%)")
            plt.xlabel("Measurement #")
            plt.ylabel("Error Rate (%)")
            plt.axhline(y=self.error_rate_threshold * 100, color='r', linestyle='--')
            plt.grid(True)
            plt.savefig(os.path.join(output_dir, "error_rates.png"))
            plt.close()
        
        # Usage by hour (last 24 hours)
        now = datetime.now()
        hour_keys = [
            (now - timedelta(hours=i)).strftime("%Y-%m-%d %H:00")
            for i in range(24, 0, -1)
        ]
        
        hour_values = [self.usage_by_hour.get(key, 0) for key in hour_keys]
        
        plt.figure(figsize=(14, 6))
        plt.bar(range(len(hour_keys)), hour_values)
        plt.title("API Usage by Hour (Last 24 Hours)")
        plt.xlabel("Hour")
        plt.ylabel("Request Count")
        plt.xticks(range(len(hour_keys)), [key.split()[1] for key in hour_keys], rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "usage_by_hour.png"))
        plt.close()
        
        # Usage by day (last 30 days)
        day_keys = [
            (now - timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range(30, 0, -1)
        ]
        
        day_values = [self.usage_by_day.get(key, 0) for key in day_keys]
        
        plt.figure(figsize=(14, 6))
        plt.bar(range(len(day_keys)), day_values)
        plt.title("API Usage by Day (Last 30 Days)")
        plt.xlabel("Day")
        plt.ylabel("Request Count")
        plt.xticks(range(len(day_keys)), [key[5:] for key in day_keys], rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "usage_by_day.png"))
        plt.close()
        
        # Status code distribution
        if self.status_codes:
            labels = list(self.status_codes.keys())
            values = list(self.status_codes.values())
            
            plt.figure(figsize=(10, 6))
            plt.bar(range(len(labels)), values)
            plt.title("Status Code Distribution")
            plt.xlabel("Status Code")
            plt.ylabel("Count")
            plt.xticks(range(len(labels)), labels)
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, "status_codes.png"))
            plt.close()
        
        logger.info(f"Visualizations saved to {output_dir}")
    
    def _monitoring_loop(self):
        """Internal monitoring loop that runs periodically."""
        while self.monitoring_active:
            try:
                # Perform health check
                is_healthy, metrics = self.health_check()
                
                # Log health status
                if is_healthy:
                    logger.info(f"Health check passed: {metrics['response_time_ms']:.2f}ms")
                else:
                    logger.warning(f"Health check failed: {metrics}")
                
                # Check quota if available
                if 'quota_info' in metrics and metrics['quota_info']:
                    self._check_quota_alerts(metrics['quota_info'])
                
                # Generate periodic report (daily)
                current_hour = datetime.now().hour
                if current_hour == 0:  # Midnight
                    self._generate_daily_report()
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
            
            # Sleep until next check
            time.sleep(self.check_interval_seconds)
    
    def _check_alerts(
        self,
        response_time_ms: float,
        error_rate: float,
        endpoint: str
    ):
        """Check if any metrics trigger alerts."""
        now = datetime.now()
        
        # Check response time alert
        if (response_time_ms > self.response_time_threshold_ms and
            (now - self.last_alerts["response_time"]).total_seconds() > self.alert_cooldown_hours * 3600):
            
            self.last_alerts["response_time"] = now
            message = (f"ALERT: High response time detected ({response_time_ms:.2f}ms) "
                      f"for endpoint {endpoint}. Threshold: {self.response_time_threshold_ms}ms")
            
            logger.warning(message)
            self._send_alert("High Response Time", message)
        
        # Check error rate alert
        if (error_rate > self.error_rate_threshold and
            (now - self.last_alerts["error_rate"]).total_seconds() > self.alert_cooldown_hours * 3600):
            
            self.last_alerts["error_rate"] = now
            message = (f"ALERT: High error rate detected ({error_rate:.2%}). "
                      f"Threshold: {self.error_rate_threshold:.2%}")
            
            logger.warning(message)
            self._send_alert("High Error Rate", message)
    
    def _check_quota_alerts(self, quota_info: Dict[str, Any]):
        """Check if quota usage triggers alerts."""
        now = datetime.now()
        
        # Check for quota alert
        if 'used' in quota_info and 'limit' in quota_info:
            used = quota_info['used']
            limit = quota_info['limit']
            
            if limit > 0:
                usage_ratio = used / limit
                
                if (usage_ratio > self.quota_warning_threshold and
                    (now - self.last_alerts["quota"]).total_seconds() > self.alert_cooldown_hours * 3600):
                    
                    self.last_alerts["quota"] = now
                    message = (f"ALERT: Approaching API quota limit. "
                              f"Used: {used}/{limit} ({usage_ratio:.2%}). "
                              f"Threshold: {self.quota_warning_threshold:.2%}")
                    
                    logger.warning(message)
                    self._send_alert("Quota Warning", message)
    
    def _generate_daily_report(self):
        """Generate and send a daily report."""
        summary = self.get_performance_summary()
        
        # Generate report text
        report = f"""
        Pyunto Intelligence Daily Performance Report
        Date: {datetime.now().strftime("%Y-%m-%d")}
        
        API Usage Summary:
        - Total requests today: {summary['usage']['today']}
        - Total requests yesterday: {summary['usage']['yesterday']}
        - Last 7 days: {summary['usage']['last_7_days']}
        
        Performance Metrics:
        - Average response time: {summary['response_time']['average_ms']}ms
        - 95th percentile response time: {summary['response_time']['p95_ms']}ms
        - Current error rate: {summary['error_rate']['current']}%
        
        Status Code Distribution:
        {json.dumps(summary['status_codes'], indent=2)}
        
        This is an automated report from the Pyunto Intelligence monitoring system.
        """
        
        # Send report
        if self.alert_email:
            self._send_email(
                subject="Pyunto Intelligence Daily Performance Report",
                body=report
            )
        
        # Save visualizations
        if self.enable_visualization:
            self.visualize_metrics()
        
        logger.info("Daily report generated and sent")
    
    def _send_alert(self, alert_type: str, message: str):
        """Send an alert via configured channels."""
        if self.alert_email:
            subject = f"Pyunto Intelligence Alert: {alert_type}"
            self._send_email(subject, message)
        
        if self.alert_webhook:
            self._send_webhook(alert_type, message)
    
    def _send_email(self, subject: str, body: str):
        """Send an email alert.
        
        Args:
            subject: Email subject
            body: Email body
        """
        if not self.alert_email:
            logger.warning("No alert email configured")
            return
        
        # Check if SMTP settings are configured
        smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        smtp_user = os.environ.get("SMTP_USER")
        smtp_pass = os.environ.get("SMTP_PASS")
        
        if not smtp_user or not smtp_pass:
            logger.warning("SMTP credentials not configured, cannot send email alert")
            return
        
        sender_email = smtp_user
        receiver_email = self.alert_email
        
        # Create message
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = subject
        
        # Attach body
        message.attach(MIMEText(body, "plain"))
        
        try:
            # Connect to SMTP server
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_pass)
            
            # Send email
            server.sendmail(sender_email, receiver_email, message.as_string())
            server.quit()
            
            logger.info(f"Alert email sent to {receiver_email}")
            
        except Exception as e:
            logger.error(f"Failed to send alert email: {e}")
    
    def _send_webhook(self, alert_type: str, message: str):
        """Send an alert to a webhook.
        
        Args:
            alert_type: Type of alert
            message: Alert message
        """
        if not self.alert_webhook:
            logger.warning("No alert webhook configured")
            return
        
        payload = {
            "type": alert_type,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "service": "PyuntoMonitor"
        }
        
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
    
    def _save_metrics(self):
        """Save current metrics to file."""
        try:
            # Create metrics object
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "response_times": list(self.response_times),
                "error_rates": list(self.error_rates),
                "usage_by_hour": dict(self.usage_by_hour),
                "usage_by_day": dict(self.usage_by_day),
                "status_codes": dict(self.status_codes)
            }
            
            # Save to file (append mode)
            with open(self.metrics_file, "a") as f:
                f.write(json.dumps(metrics) + "\n")
                
            logger.debug("Metrics saved to file")
            
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")
    
    def _load_metrics(self):
        """Load metrics from file if it exists."""
        if not os.path.exists(self.metrics_file):
            logger.info(f"No metrics file found at {self.metrics_file}")
            return
        
        try:
            with open(self.metrics_file, "r") as f:
                # Read the last line (most recent metrics)
                lines = f.readlines()
                if not lines:
                    return
                
                latest_metrics = json.loads(lines[-1])
                
                # Restore metrics
                self.response_times = deque(latest_metrics["response_times"], maxlen=1000)
                self.error_rates = deque(latest_metrics["error_rates"], maxlen=100)
                self.usage_by_hour = defaultdict(int, latest_metrics["usage_by_hour"])
                self.usage_by_day = defaultdict(int, latest_metrics["usage_by_day"])
                self.status_codes = defaultdict(int, latest_metrics["status_codes"])
                
                logger.info(f"Loaded metrics from {self.metrics_file}")
                
        except Exception as e:
            logger.error(f"Failed to load metrics: {e}")


class UsageTracker:
    """Track and analyze Pyunto Intelligence API usage."""
    
    def __init__(
        self,
        api_key: str,
        plan_limits: Optional[Dict[str, int]] = None,
        data_file: str = "pyunto_usage.jsonl"
    ):
        """
        Initialize the usage tracker.
        
        Args:
            api_key: Pyunto Intelligence API key
            plan_limits: Optional dict with plan limits
            data_file: File to store usage data
        """
        self.api_key = api_key
        self.data_file = data_file
        
        # Set default plan limits if not provided
        self.plan_limits = plan_limits or {
            "STANDARD": 3000,      # 3,000 calls/month
            "PRO": 40000,          # 40,000 calls/month
            "ENTERPRISE": 300000   # 300,000 calls/month
        }
        
        # Usage data
        self.current_month_usage = 0
        self.usage_by_day = defaultdict(int)
        self.usage_by_hour = defaultdict(int)
        self.usage_by_endpoint = defaultdict(int)
        self.usage_by_assistant = defaultdict(int)
        
        # Load existing usage data if available
        self._load_usage_data()
    
    def track_call(
        self,
        endpoint: str,
        assistant_id: Optional[str] = None,
        status_code: int = 200
    ):
        """
        Track an API call.
        
        Args:
            endpoint: API endpoint called
            assistant_id: Optional assistant ID
            status_code: HTTP status code
        """
        timestamp = datetime.now()
        
        # Skip non-billable calls (e.g., health checks)
        if endpoint.endswith("/health") or endpoint.endswith("/quota"):
            return
        
        # Update usage counters
        self.current_month_usage += 1
        
        day_key = timestamp.strftime("%Y-%m-%d")
        hour_key = timestamp.strftime("%Y-%m-%d %H:00")
        
        self.usage_by_day[day_key] += 1
        self.usage_by_hour[hour_key] += 1
        self.usage_by_endpoint[endpoint] += 1
        
        if assistant_id:
            self.usage_by_assistant[assistant_id] += 1
        
        # Save usage data periodically (every 10 calls)
        if self.current_month_usage % 10 == 0:
            self._save_usage_data()
    
    def get_current_usage_stats(self) -> Dict[str, Any]:
        """
        Get current usage statistics.
        
        Returns:
            Dict with usage statistics
        """
        now = datetime.now()
        current_month = now.strftime("%Y-%m")
        
        # Calculate monthly usage
        monthly_usage = sum(
            count for day, count in self.usage_by_day.items()
            if day.startswith(current_month)
        )
        
        # Calculate daily average (last 30 days)
        last_30_days = [
            (now - timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range(30)
        ]
        
        last_30_days_usage = sum(
            self.usage_by_day.get(day, 0) for day in last_30_days
        )
        
        daily_average = last_30_days_usage / 30 if last_30_days_usage > 0 else 0
        
        # Calculate remaining quota (assuming STANDARD plan by default)
        plan = os.environ.get("PYUNTO_PLAN", "STANDARD")
        monthly_limit = self.plan_limits.get(plan, 3000)
        
        remaining_quota = max(0, monthly_limit - monthly_usage)
        
        # Calculate days until quota exhaustion (at current rate)
        days_in_month = 30  # Approximate
        days_passed = now.day
        days_remaining = days_in_month - days_passed
        
        projected_usage = (monthly_usage / days_passed) * days_in_month if days_passed > 0 else 0
        
        if daily_average > 0:
            days_until_exhaustion = remaining_quota / daily_average
        else:
            days_until_exhaustion = float('inf')
        
        # Top assistants by usage
        top_assistants = sorted(
            self.usage_by_assistant.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            "current_month": current_month,
            "current_month_usage": monthly_usage,
            "monthly_limit": monthly_limit,
            "remaining_quota": remaining_quota,
            "quota_usage_percentage": (monthly_usage / monthly_limit) * 100 if monthly_limit > 0 else 0,
            "daily_average_last_30d": round(daily_average, 2),
            "projected_monthly_usage": round(projected_usage, 2),
            "projected_percentage": (projected_usage / monthly_limit) * 100 if monthly_limit > 0 else 0,
            "days_until_quota_exhaustion": round(days_until_exhaustion, 1) if days_until_exhaustion != float('inf') else None,
            "top_assistants": dict(top_assistants),
            "top_endpoints": dict(
                sorted(
                    self.usage_by_endpoint.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5]
            )
        }
    
    def visualize_usage(self, output_dir: str = "reports"):
        """
        Generate visualizations of usage data.
        
        Args:
            output_dir: Directory to save visualizations
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Daily usage (last 30 days)
        now = datetime.now()
        days = [
            (now - timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range(29, -1, -1)
        ]
        
        values = [self.usage_by_day.get(day, 0) for day in days]
        
        plt.figure(figsize=(14, 6))
        plt.bar(range(len(days)), values)
        plt.title("Daily API Usage (Last 30 Days)")
        plt.xlabel("Date")
        plt.ylabel("API Calls")
        plt.xticks(range(0, len(days), 3), [days[i][5:] for i in range(0, len(days), 3)], rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "daily_usage.png"))
        plt.close()
        
        # Hourly usage (last 24 hours)
        hours = [
            (now - timedelta(hours=i)).strftime("%Y-%m-%d %H:00")
            for i in range(23, -1, -1)
        ]
        
        hour_values = [self.usage_by_hour.get(hour, 0) for hour in hours]
        
        plt.figure(figsize=(14, 6))
        plt.bar(range(len(hours)), hour_values)
        plt.title("Hourly API Usage (Last 24 Hours)")
        plt.xlabel("Hour")
        plt.ylabel("API Calls")
        plt.xticks(range(0, len(hours), 2), [hours[i].split()[1] for i in range(0, len(hours), 2)], rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "hourly_usage.png"))
        plt.close()
        
        # Monthly quota usage
        current_stats = self.get_current_usage_stats()
        
        used = current_stats["current_month_usage"]
        remaining = current_stats["remaining_quota"]
        
        plt.figure(figsize=(8, 8))
        plt.pie(
            [used, remaining],
            labels=["Used", "Remaining"],
            colors=["#ff9999", "#66b3ff"],
            autopct='%1.1f%%',
            startangle=90
        )
        plt.axis('equal')
        plt.title(f"Monthly Quota Usage ({current_stats['quota_usage_percentage']:.1f}%)")
        plt.savefig(os.path.join(output_dir, "quota_usage.png"))
        plt.close()
        
        # Usage by assistant
        if self.usage_by_assistant:
            assistants = list(self.usage_by_assistant.keys())
            assistant_values = list(self.usage_by_assistant.values())
            
            plt.figure(figsize=(10, 6))
            plt.bar(range(len(assistants)), assistant_values)
            plt.title("API Usage by Assistant")
            plt.xlabel("Assistant")
            plt.ylabel("API Calls")
            plt.xticks(range(len(assistants)), [a[:8] + "..." for a in assistants], rotation=45)
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, "assistant_usage.png"))
            plt.close()
        
        logger.info(f"Usage visualizations saved to {output_dir}")
    
    def _save_usage_data(self):
        """Save usage data to file."""
        try:
            # Create usage data object
            usage_data = {
                "timestamp": datetime.now().isoformat(),
                "current_month_usage": self.current_month_usage,
                "usage_by_day": dict(self.usage_by_day),
                "usage_by_hour": dict(self.usage_by_hour),
                "usage_by_endpoint": dict(self.usage_by_endpoint),
                "usage_by_assistant": dict(self.usage_by_assistant)
            }
            
            # Save to file (append mode)
            with open(self.data_file, "a") as f:
                f.write(json.dumps(usage_data) + "\n")
                
            logger.debug("Usage data saved to file")
            
        except Exception as e:
            logger.error(f"Failed to save usage data: {e}")
    
    def _load_usage_data(self):
        """Load usage data from file if it exists."""
        if not os.path.exists(self.data_file):
            logger.info(f"No usage data file found at {self.data_file}")
            return
        
        try:
            with open(self.data_file, "r") as f:
                # Read the last line (most recent data)
                lines = f.readlines()
                if not lines:
                    return
                
                latest_data = json.loads(lines[-1])
                
                # Restore usage data
                self.current_month_usage = latest_data["current_month_usage"]
                self.usage_by_day = defaultdict(int, latest_data["usage_by_day"])
                self.usage_by_hour = defaultdict(int, latest_data["usage_by_hour"])
                self.usage_by_endpoint = defaultdict(int, latest_data["usage_by_endpoint"])
                self.usage_by_assistant = defaultdict(int, latest_data["usage_by_assistant"])
                
                logger.info(f"Loaded usage data from {self.data_file}")
                
        except Exception as e:
            logger.error(f"Failed to load usage data: {e}")


# Example usage
if __name__ == "__main__":
    # Get API key from environment
    api_key = os.environ.get("PYUNTO_API_KEY")
    
    if not api_key:
        logger.error("No API key found. Set PYUNTO_API_KEY environment variable.")
        exit(1)
    
    # Initialize monitor
    monitor = PyuntoMonitor(
        api_key=api_key,
        alert_email=os.environ.get("ALERT_EMAIL"),
        enable_visualization=True
    )
    
    # Configure monitoring
    monitor.setup_basic_monitoring(
        check_interval_seconds=300,  # Check every 5 minutes
        response_time_threshold_ms=2000,  # Alert if response time exceeds 2 seconds
        error_rate_threshold=0.05,  # Alert if error rate exceeds 5%
        quota_warning_threshold=0.8  # Alert when 80% of quota is consumed
    )
    
    # Initialize usage tracker
    tracker = UsageTracker(api_key=api_key)
    
    # Start monitoring
    try:
        monitor.start()
        logger.info("Monitoring started. Press Ctrl+C to stop.")
        
        # Example of manually tracking calls
        for i in range(10):
            # Simulate API calls
            endpoint = "/api/i/v1" if i % 2 == 0 else "/api/i/v1/analyze"
            assistant_id = f"asst_{'a' if i % 3 == 0 else 'b'}"
            
            # Track API calls
            tracker.track_call(endpoint, assistant_id)
            
            # Sleep briefly
            time.sleep(0.5)
        
        # Generate usage report
        usage_stats = tracker.get_current_usage_stats()
        logger.info(f"Current usage stats: {json.dumps(usage_stats, indent=2)}")
        
        # Visualize usage
        tracker.visualize_usage()
        
        # Run indefinitely
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Stopping monitoring...")
        monitor.stop()
        logger.info("Monitoring stopped.")
