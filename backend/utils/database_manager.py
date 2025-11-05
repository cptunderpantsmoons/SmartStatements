"""
Database Manager for AI Financial Statement Generation System
Handles Supabase PostgreSQL operations and local SQLite caching
"""
import json
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from supabase import create_client

from ..config.settings import config


class DatabaseManager:
    """Manages database operations for Supabase and local SQLite"""
    
    def __init__(self):
        """Initialize database connections"""
        # Supabase client for main data storage
        self.supabase = create_client(
            supabase_url=config.supabase_url,
            supabase_key=config.supabase_service_key
        )
        
        # Local SQLite for caching and audit trail
        self.init_sqlite_cache()
    
    def init_sqlite_cache(self):
        """Initialize local SQLite cache database"""
        import sqlite3
        
        conn = sqlite3.connect(config.sqlite_db_path)
        cursor = conn.cursor()
        
        # Create cache table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                input_hash TEXT UNIQUE NOT NULL,
                model_name TEXT NOT NULL,
                response TEXT NOT NULL,
                token_count INTEGER,
                cost_usd DECIMAL(10,4),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            )
        ''')
        
        # Create metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS local_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT NOT NULL,
                operation_type TEXT NOT NULL,
                latency_seconds DECIMAL(8,3),
                token_count INTEGER,
                cost_usd DECIMAL(10,4),
                success BOOLEAN DEFAULT TRUE,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_report(self, user_id: str, year: int, file_path: str) -> str:
        """Create new report record in Supabase"""
        report_id = str(uuid.uuid4())
        
        try:
            result = self.supabase.table('reports').insert({
                'id': report_id,
                'user_id': user_id,
                'year': year,
                'status': 'processing',
                'file_path': file_path,
                'file_type': self._get_file_type(file_path),
                'processing_log': []
            }).execute()
            
            return report_id
            
        except Exception as e:
            raise Exception(f"Failed to create report: {str(e)}")
    
    def update_report_status(self, report_id: str, status: str, error_message: str = None):
        """Update report status"""
        try:
            update_data = {'status': status}
            if error_message:
                update_data['error_message'] = error_message
            
            self.supabase.table('reports').update(update_data).eq('id', report_id).execute()
            
        except Exception as e:
            print(f"Failed to update report status: {str(e)}")
    
    def update_report_completion(self, report_id: str, raw_data: Dict, mapping_result: Dict, qa_report: Dict, cert_data: Dict):
        """Update report with completion data"""
        try:
            # Update main report
            self.supabase.table('reports').update({
                'status': 'ready' if qa_report.get('overall_status') == 'PASS' else 'review_needed',
                'raw_data': raw_data,
                'mapping': mapping_result,
                'qa_report': qa_report
            }).eq('id', report_id).execute()
            
            # Create verification record
            verification_data = {
                'report_id': report_id,
                'steps': qa_report.get('checks', []),
                'math_proofs': qa_report.get('mathematical_proofs', {}),
                'cert_hash': self._generate_hash(cert_data.get('certificate_html', '')),
                'cert_file_path': cert_data.get('file_path'),
                'overall_score': qa_report.get('overall_score', 0),
                'compliance_status': qa_report.get('overall_status', 'REVIEW')
            }
            
            self.supabase.table('verifications').insert(verification_data).execute()
            
        except Exception as e:
            print(f"Failed to update report completion: {str(e)}")
    
    def get_report_status(self, report_id: str) -> Dict[str, Any]:
        """Get current status of a report"""
        try:
            result = self.supabase.table('reports').select('*').eq('id', report_id).execute()
            
            if result.data:
                return result.data[0]
            else:
                return {"error": "Report not found"}
                
        except Exception as e:
            return {"error": f"Failed to get report status: {str(e)}"}
    
    def get_user_reports(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all reports for a user"""
        try:
            result = self.supabase.table('user_reports_summary').select('*').eq('user_id', user_id).execute()
            return result.data or []
            
        except Exception as e:
            print(f"Failed to get user reports: {str(e)}")
            return []
    
    def cache_ai_response(self, input_hash: str, model_name: str, response: Dict, token_count: int = None, cost_usd: float = None):
        """Cache AI response in local SQLite"""
        import sqlite3
        from datetime import timedelta
        
        try:
            conn = sqlite3.connect(config.sqlite_db_path)
            cursor = conn.cursor()
            
            expires_at = datetime.now(timezone.utc) + timedelta(hours=config.cache_ttl_hours)
            
            cursor.execute('''
                INSERT OR REPLACE INTO ai_cache 
                (input_hash, model_name, response, token_count, cost_usd, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                input_hash, 
                model_name, 
                json.dumps(response), 
                token_count, 
                cost_usd, 
                expires_at.isoformat()
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Failed to cache AI response: {str(e)}")
    
    def get_cached_response(self, input_hash: str, model_name: str) -> Optional[Dict]:
        """Get cached AI response if available and not expired"""
        import sqlite3
        
        try:
            conn = sqlite3.connect(config.sqlite_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT response FROM ai_cache 
                WHERE input_hash = ? AND model_name = ? AND expires_at > datetime('now')
            ''', (input_hash, model_name))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return json.loads(result[0])
            else:
                return None
                
        except Exception as e:
            print(f"Failed to get cached response: {str(e)}")
            return None
    
    def record_metric(self, model_name: str, operation_type: str, latency_seconds: float, 
                   token_count: int = None, cost_usd: float = None, success: bool = True, 
                   error_message: str = None):
        """Record performance metric"""
        import sqlite3
        
        try:
            # Record in local SQLite
            conn = sqlite3.connect(config.sqlite_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO local_metrics 
                (model_name, operation_type, latency_seconds, token_count, cost_usd, success, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (model_name, operation_type, latency_seconds, token_count, cost_usd, success, error_message))
            
            conn.commit()
            conn.close()
            
            # Also record in Supabase if successful
            if success:
                try:
                    self.supabase.table('metrics').insert({
                        'model_name': model_name,
                        'operation_type': operation_type,
                        'latency_seconds': latency_seconds,
                        'token_count': token_count,
                        'cost_usd': cost_usd,
                        'success': success
                    }).execute()
                except:
                    pass  # Ignore Supabase errors for metrics
                    
        except Exception as e:
            print(f"Failed to record metric: {str(e)}")
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics"""
        try:
            result = self.supabase.table('system_metrics').select('*').execute()
            return result.data or []
            
        except Exception as e:
            print(f"Failed to get system metrics: {str(e)}")
            return []
    
    def clean_expired_cache(self):
        """Clean expired cache entries"""
        import sqlite3
        
        try:
            conn = sqlite3.connect(config.sqlite_db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM ai_cache WHERE expires_at <= datetime("now")')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Failed to clean expired cache: {str(e)}")
    
    def _get_file_type(self, file_path: str) -> str:
        """Determine file type from path"""
        if file_path.endswith('.pdf'):
            return 'pdf'
        elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
            return 'excel'
        else:
            return 'unknown'
    
    def _generate_hash(self, content: str) -> str:
        """Generate SHA256 hash"""
        import hashlib
        return hashlib.sha256(content.encode()).hexdigest()
    
    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user preferences"""
        try:
            result = self.supabase.table('user_preferences').select('*').eq('user_id', user_id).execute()
            
            if result.data:
                return result.data[0]
            else:
                # Create default preferences
                default_prefs = {
                    'user_id': user_id,
                    'default_format': {},
                    'notification_settings': {'email': True, 'push': False},
                    'auto_save': True
                }
                
                self.supabase.table('user_preferences').insert(default_prefs).execute()
                return default_prefs
                
        except Exception as e:
            print(f"Failed to get user preferences: {str(e)}")
            return {}
    
    def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]):
        """Update user preferences"""
        try:
            self.supabase.table('user_preferences').update(preferences).eq('user_id', user_id).execute()
            
        except Exception as e:
            print(f"Failed to update user preferences: {str(e)}")
