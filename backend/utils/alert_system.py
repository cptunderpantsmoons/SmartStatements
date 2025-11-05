"""
Alert System for AI Financial Statement Generation System
Handles email notifications and alerts for processing failures
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from ..config.settings import config


class AlertSystem:
    """Manages email alerts and notifications"""
    
    def __init__(self):
        """Initialize alert system"""
        self.smtp_server = config.smtp_server
        self.smtp_port = config.smtp_port
        self.smtp_username = config.smtp_username
        self.smtp_password = config.smtp_password
        self.alert_email = config.alert_email
        
        # Check if email configuration is available
        self.email_enabled = all([
            self.smtp_server,
            self.smtp_username,
            self.smtp_password,
            self.alert_email
        ])
        
        if not self.email_enabled:
            print("Email alerts not configured - alerts will be logged only")
    
    def send_alert(self, user_id: str, qa_report: Dict[str, Any], report_id: str):
        """Send alert for processing issues"""
        try:
            # Determine alert level based on QA report
            alert_level = self._determine_alert_level(qa_report)
            
            # Create alert content
            subject = f"[FS PIPELINE] {alert_level} - Report {report_id}"
            body = self._create_alert_body(user_id, qa_report, report_id, alert_level)
            
            # Send email if configured
            if self.email_enabled:
                self._send_email(subject, body)
            else:
                # Log alert instead
                self._log_alert(subject, body, alert_level)
                
        except Exception as e:
            print(f"Failed to send alert: {str(e)}")
    
    def send_completion_notification(self, user_id: str, report_id: str, processing_time: float, score: float):
        """Send notification for successful completion"""
        try:
            subject = f"[FS PIPELINE] SUCCESS - Report {report_id}"
            body = self._create_success_body(user_id, report_id, processing_time, score)
            
            if self.email_enabled:
                self._send_email(subject, body)
            else:
                self._log_alert(subject, body, "INFO")
                
        except Exception as e:
            print(f"Failed to send completion notification: {str(e)}")
    
    def send_system_alert(self, message: str, level: str = "ERROR"):
        """Send system-level alert"""
        try:
            subject = f"[FS PIPELINE] SYSTEM {level}"
            body = f"""
System Alert: {level.upper()}

Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}

Message:
{message}

Please check the system status and logs.
            """.strip()
            
            if self.email_enabled:
                self._send_email(subject, body)
            else:
                self._log_alert(subject, body, level)
                
        except Exception as e:
            print(f"Failed to send system alert: {str(e)}")
    
    def _determine_alert_level(self, qa_report: Dict[str, Any]) -> str:
        """Determine alert level from QA report"""
        status = qa_report.get('overall_status', 'UNKNOWN')
        score = qa_report.get('overall_score', 0)
        
        if status == 'FAIL':
            return 'CRITICAL'
        elif status == 'REVIEW':
            return 'WARNING'
        elif score < 70:
            return 'WARNING'
        elif score < 85:
            return 'INFO'
        else:
            return 'SUCCESS'
    
    def _create_alert_body(self, user_id: str, qa_report: Dict[str, Any], report_id: str, alert_level: str) -> str:
        """Create alert email body"""
        status = qa_report.get('overall_status', 'UNKNOWN')
        score = qa_report.get('overall_score', 0)
        checks = qa_report.get('checks', [])
        critical_issues = [check for check in checks if check.get('status') == 'FAIL']
        
        body = f"""
Financial Statement Processing Alert

Report ID: {report_id}
User ID: {user_id}
Alert Level: {alert_level}
Processing Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}

QA Results:
- Overall Status: {status}
- Overall Score: {score}/100
- Critical Issues: {len(critical_issues)}

"""
        
        if critical_issues:
            body += "Critical Issues Found:\n"
            for i, issue in enumerate(critical_issues[:5], 1):  # Limit to first 5
                body += f"""
{i}. {issue.get('check_name', 'Unknown Check')}
   Status: {issue.get('status', 'Unknown')}
   Details: {issue.get('details', 'No details available')}
   Recommendation: {issue.get('recommendations', ['No recommendations'])[0] if issue.get('recommendations') else 'No recommendations'}
"""
        
        body += f"""
Action Required:
- Review the QA report for detailed findings
- Address critical issues before finalizing statements
- Contact support if assistance is needed

Access your report at: https://your-app.com/reports/{report_id}

This is an automated alert from the AI Financial Statement Generation System.
        """.strip()
        
        return body
    
    def _create_success_body(self, user_id: str, report_id: str, processing_time: float, score: float) -> str:
        """Create success notification body"""
        return f"""
Financial Statement Processing Completed Successfully

Report ID: {report_id}
User ID: {user_id}
Completion Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
Processing Duration: {processing_time:.2f} seconds
Quality Score: {score}/100

Your financial statements are ready for review and download.

Access your report at: https://your-app.com/reports/{report_id}

This is an automated notification from the AI Financial Statement Generation System.
        """.strip()
    
    def _send_email(self, subject: str, body: str):
        """Send email using SMTP"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.smtp_username
            msg['To'] = self.alert_email
            msg['Subject'] = subject
            
            # Attach body
            msg.attach(MIMEText(body, 'plain'))
            
            # Create SMTP session
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.smtp_username, self.smtp_password)
                text = msg.as_string()
                server.sendmail(self.smtp_username, self.alert_email, text)
                
            print(f"Alert email sent: {subject}")
            
        except Exception as e:
            print(f"Failed to send email: {str(e)}")
            # Fallback to logging
            self._log_alert(subject, body, "EMAIL_FAILED")
    
    def _log_alert(self, subject: str, body: str, level: str):
        """Log alert when email is not available"""
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        
        log_entry = f"""
[{timestamp}] {level}: {subject}

{body}

---
        """.strip()
        
        print(log_entry)
        
        # Could also write to file or external logging system
        # For now, just print to console
    
    def test_email_configuration(self) -> Dict[str, Any]:
        """Test email configuration"""
        if not self.email_enabled:
            return {
                'success': False,
                'error': 'Email not properly configured',
                'missing_settings': self._get_missing_settings()
            }
        
        try:
            test_subject = "[FS PIPELINE] TEST - Email Configuration"
            test_body = f"""
This is a test email to verify the alert system configuration.

Test Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
SMTP Server: {self.smtp_server}
SMTP Port: {self.smtp_port}
From: {self.smtp_username}
To: {self.alert_email}

If you receive this email, the alert system is working correctly.
            """.strip()
            
            self._send_email(test_subject, test_body)
            
            return {
                'success': True,
                'message': 'Test email sent successfully',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def _get_missing_settings(self) -> list:
        """Get list of missing email settings"""
        missing = []
        
        if not self.smtp_server:
            missing.append('SMTP_SERVER')
        if not self.smtp_username:
            missing.append('SMTP_USERNAME')
        if not self.smtp_password:
            missing.append('SMTP_PASSWORD')
        if not self.alert_email:
            missing.append('ALERT_EMAIL')
            
        return missing
    
    def get_alert_status(self) -> Dict[str, Any]:
        """Get current alert system status"""
        return {
            'email_enabled': self.email_enabled,
            'smtp_server': self.smtp_server,
            'smtp_port': self.smtp_port,
            'smtp_username': self.smtp_username,
            'alert_email': self.alert_email,
            'missing_settings': self._get_missing_settings() if not self.email_enabled else [],
            'test_result': None
        }
