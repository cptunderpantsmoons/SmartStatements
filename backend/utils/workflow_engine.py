"""
AI Financial Statement Generation Workflow Engine
Orchestrates the complete pipeline from file input to verified output
"""
import os
import json
import time
import hashlib
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import sqlite3
from pathlib import Path

from ..config.settings import config
from ..models.gemini_client import GeminiClient
from ..models.grok_client import GrokClient
from .database_manager import DatabaseManager
from .file_monitor import FileMonitor
from .metrics_collector import MetricsCollector
from .alert_system import AlertSystem


class WorkflowEngine:
    """Main workflow engine for AI Financial Statement Generation"""
    
    def __init__(self):
        """Initialize workflow engine with all components"""
        self.gemini_client = GeminiClient()
        self.grok_client = GrokClient()
        self.db_manager = DatabaseManager()
        self.file_monitor = FileMonitor()
        self.metrics = MetricsCollector()
        self.alert_system = AlertSystem()
        
        # Ensure directories exist
        os.makedirs(config.input_directory, exist_ok=True)
        os.makedirs(config.output_directory, exist_ok=True)
        
    def process_file(self, file_path: str, user_id: str, year: int = 2025) -> Dict[str, Any]:
        """
        Main processing pipeline for financial statement generation
        """
        start_time = time.time()
        processing_steps = []
        math_proofs = {}
        
        try:
            # Create report record in database
            report_id = self.db_manager.create_report(user_id, year, file_path)
            
            # Step 1: File Analysis and Routing
            file_info = self._analyze_file(file_path)
            processing_steps.append({
                "step": 1,
                "name": "File Analysis",
                "model": "system",
                "input_hash": self._get_file_hash(file_path),
                "output_summary": f"File type: {file_info['type']}, Size: {file_info['size_mb']}MB",
                "latency_seconds": 0.1,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Step 2: Extract 2024 Template (if needed)
            template_data = None
            if file_info.get('is_template', False):
                template_data = self._extract_template_data(file_path, processing_steps)
            else:
                # Load existing template data
                template_data = self._load_template_data()
            
            # Step 3: Extract and Heal 2025 Data
            raw_data, healed_data = self._extract_and_heal_data(file_path, file_info, processing_steps)
            
            # Step 4: Semantic Account Mapping
            mapping_result = self._perform_account_mapping(template_data, healed_data, processing_steps)
            
            # Step 5: Generate Financial Statements
            generated_excel_path = self._generate_statements(template_data, healed_data, mapping_result, processing_steps)
            
            # Step 6: Quality Assurance Audit
            qa_report = self._perform_quality_assurance(generated_excel_path, template_data, mapping_result, healed_data, processing_steps)
            
            # Step 7: Generate Verification Certificate
            cert_data = self._generate_verification_certificate(qa_report, processing_steps, math_proofs)
            
            # Step 8: Update Database with Results
            self._update_report_completion(report_id, healed_data, mapping_result, qa_report, cert_data)
            
            # Step 9: Send Alerts if Needed
            if qa_report.get('overall_status') in ['FAIL', 'REVIEW']:
                self.alert_system.send_alert(user_id, qa_report, report_id)
            
            total_time = time.time() - start_time
            
            # Record metrics
            self.metrics.record_workflow_completion(total_time, len(processing_steps), qa_report.get('overall_score', 0))
            
            return {
                "status": "success",
                "report_id": report_id,
                "processing_time_seconds": total_time,
                "statements_file": generated_excel_path,
                "certificate_file": cert_data.get('file_path'),
                "qa_report": qa_report,
                "processing_steps": processing_steps,
                "math_proofs": math_proofs
            }
            
        except Exception as e:
            error_msg = f"Workflow failed: {str(e)}"
            print(error_msg)
            
            # Record error in database
            if 'report_id' in locals():
                self.db_manager.update_report_status(report_id, 'error', error_msg)
            
            # Record error metrics
            self.metrics.record_workflow_error(str(e))
            
            return {
                "status": "error",
                "error": error_msg,
                "processing_time_seconds": time.time() - start_time,
                "processing_steps": processing_steps
            }
    
    def _analyze_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze input file to determine processing route"""
        file_ext = Path(file_path).suffix.lower()
        file_size = os.path.getsize(file_path)
        
        # Check if it's a template (2024) or new data (2025)
        filename = os.path.basename(file_path).lower()
        is_template = '2024' in filename or 'template' in filename
        
        return {
            "type": file_ext,
            "size_mb": round(file_size / (1024 * 1024), 2),
            "is_template": is_template,
            "year": 2024 if is_template else 2025
        }
    
    def _extract_template_data(self, file_path: str, processing_steps: List[Dict]) -> Dict[str, Any]:
        """Extract template data from 2024 PDF"""
        step_start = time.time()
        
        try:
            if file_path.endswith('.pdf'):
                result = self.gemini_client.extract_pdf_template(file_path)
            else:
                raise ValueError("Template must be a PDF file")
            
            processing_steps.append({
                "step": 2,
                "name": "Template Extraction",
                "model": config.gemini_pro_model,
                "input_hash": self._get_file_hash(file_path),
                "output_summary": f"Extracted {len(result.get('pages', []))} pages with {sum(len(p.get('tables', [])) for p in result.get('pages', []))} tables",
                "latency_seconds": time.time() - step_start,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return result
            
        except Exception as e:
            raise Exception(f"Template extraction failed: {str(e)}")
    
    def _load_template_data(self) -> Dict[str, Any]:
        """Load existing template data from database or default"""
        # For now, return a basic template structure
        # In production, this would load from database or cache
        return {
            "source": "default_template",
            "pages": [],
            "format": {
                "fonts": ["Arial", "Calibri"],
                "sizes": [10, 11, 12],
                "colors": ["black", "blue"]
            }
        }
    
    def _extract_and_heal_data(self, file_path: str, file_info: Dict, processing_steps: List[Dict]) -> Tuple[Dict, Any]:
        """Extract data from input file and perform data healing"""
        step_start = time.time()
        
        try:
            # Extract raw data
            if file_info['type'] == '.xlsx':
                raw_data = self._extract_excel_data(file_path)
            elif file_info['type'] == '.pdf':
                raw_data = self._extract_pdf_data(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_info['type']}")
            
            # Convert to DataFrame for healing
            df = pd.DataFrame(raw_data)
            
            # Perform data healing
            healing_result = self.gemini_client.analyze_data_quality(df)
            
            # Apply healing recommendations
            healed_df = self._apply_data_healing(df, healing_result)
            
            processing_steps.append({
                "step": 3,
                "name": "Data Extraction & Healing",
                "model": config.gemini_flash_model,
                "input_hash": self._get_file_hash(file_path),
                "output_summary": f"Processed {len(df)} rows, fixed {len(healing_result.get('issues', []))} issues",
                "latency_seconds": time.time() - step_start,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return raw_data, healed_df
            
        except Exception as e:
            raise Exception(f"Data extraction and healing failed: {str(e)}")
    
    def _extract_excel_data(self, file_path: str) -> List[Dict]:
        """Extract data from Excel file"""
        try:
            df = pd.read_excel(file_path)
            return df.to_dict('records')
        except Exception as e:
            raise Exception(f"Excel extraction failed: {str(e)}")
    
    def _extract_pdf_data(self, file_path: str) -> List[Dict]:
        """Extract data from PDF file"""
        try:
            result = self.gemini_client.extract_pdf_template(file_path)
            
            # Convert extracted tables to flat records
            records = []
            for page in result.get('pages', []):
                for table in page.get('tables', []):
                    if table.get('headers') and table.get('rows'):
                        for row in table['rows']:
                            record = dict(zip(table['headers'], row))
                            records.append(record)
            
            return records
            
        except Exception as e:
            raise Exception(f"PDF extraction failed: {str(e)}")
    
    def _apply_data_healing(self, df: pd.DataFrame, healing_result: Dict) -> pd.DataFrame:
        """Apply data healing recommendations to DataFrame"""
        healed_df = df.copy()
        
        for issue in healing_result.get('issues', []):
            row = issue.get('row')
            col = issue.get('column')
            suggested = issue.get('suggested_value')
            issue_type = issue.get('type')
            
            if row is not None and col in healed_df.columns:
                if issue_type == 'missing' and suggested is not None:
                    healed_df.at[row, col] = suggested
                elif issue_type == 'outlier':
                    # Cap at 95th percentile
                    if col in healed_df.select_dtypes(include=['number']).columns:
                        p95 = healed_df[col].quantile(0.95)
                        healed_df.at[row, col] = min(healed_df.at[row, col], p95)
                elif issue_type == 'type_error':
                    # Try to convert to proper type
                    try:
                        if healed_df[col].dtype in ['object', 'string']:
                            healed_df[col] = pd.to_numeric(healed_df[col], errors='coerce')
                    except:
                        pass
        
        return healed_df
    
    def _perform_account_mapping(self, template_data: Dict, healed_data: pd.DataFrame, processing_steps: List[Dict]) -> Dict[str, Any]:
        """Perform semantic account mapping between template and data"""
        step_start = time.time()
        
        try:
            # Extract account names from template and data
            template_accounts = self._extract_template_accounts(template_data)
            data_accounts = healed_data.columns.tolist()
            
            # Perform semantic mapping
            mapping_result = self.grok_client.semantic_account_mapping(template_accounts, data_accounts)
            
            processing_steps.append({
                "step": 4,
                "name": "Semantic Account Mapping",
                "model": config.grok_model,
                "input_hash": hashlib.sha256(json.dumps(template_accounts + data_accounts).encode()).hexdigest(),
                "output_summary": f"Mapped {len(mapping_result.get('mappings', []))} accounts with {mapping_result.get('summary', {}).get('average_confidence', 0):.2f} avg confidence",
                "latency_seconds": time.time() - step_start,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return mapping_result
            
        except Exception as e:
            raise Exception(f"Account mapping failed: {str(e)}")
    
    def _extract_template_accounts(self, template_data: Dict) -> List[str]:
        """Extract account names from template data"""
        accounts = []
        
        for page in template_data.get('pages', []):
            for table in page.get('tables', []):
                if table.get('headers'):
                    accounts.extend(table['headers'])
        
        # Remove duplicates and return
        return list(set(accounts))
    
    def _generate_statements(self, template_data: Dict, healed_data: pd.DataFrame, mapping_result: Dict, processing_steps: List[Dict]) -> str:
        """Generate final Excel statements"""
        step_start = time.time()
        
        try:
            # Generate Excel code
            code_result = self.gemini_client.generate_excel_code(template_data, healed_data.to_dict())
            
            # Save code to file for audit purposes
            code_file = os.path.join(config.output_directory, "generate_statements.py")
            with open(code_file, 'w', encoding='utf-8') as f:
                f.write(code_result['code'])
            
            # Execute code in a controlled environment
            # Create a restricted namespace for execution
            output_path = os.path.join(config.output_directory, "2025_Final.xlsx")
            
            safe_globals = {
                '__builtins__': {
                    'print': print,
                    'len': len,
                    'range': range,
                    'str': str,
                    'int': int,
                    'float': float,
                    'dict': dict,
                    'list': list,
                    'tuple': tuple,
                    'set': set,
                    'bool': bool,
                    'min': min,
                    'max': max,
                    'sum': sum,
                    'round': round,
                    'enumerate': enumerate,
                    'zip': zip
                },
                'pd': pd,
                'pandas': pd,
                'os': type('os', (), {'path': os.path, 'makedirs': os.makedirs}),
                'template_data': template_data,
                'healed_data': healed_data,
                'mapping_result': mapping_result,
                'output_path': output_path,
                'config': config
            }
            
            try:
                exec(code_result['code'], safe_globals)
            except Exception as exec_error:
                raise Exception(f"Code execution failed: {str(exec_error)}")
            
            # Verify output file was created
            if not os.path.exists(output_path):
                raise Exception(f"Expected output file not created: {output_path}")
            
            processing_steps.append({
                "step": 5,
                "name": "Statement Generation",
                "model": config.gemini_pro_model,
                "input_hash": hashlib.sha256(json.dumps(healed_data.to_dict()).encode()).hexdigest(),
                "output_summary": f"Generated Excel file: {output_path}",
                "latency_seconds": time.time() - step_start,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return output_path
            
        except Exception as e:
            raise Exception(f"Statement generation failed: {str(e)}")
    
    def _perform_quality_assurance(self, excel_path: str, template_data: Dict, mapping_result: Dict, healed_data: pd.DataFrame, processing_steps: List[Dict]) -> Dict[str, Any]:
        """Perform comprehensive QA audit"""
        step_start = time.time()
        
        try:
            qa_report = self.grok_client.quality_assurance_audit(
                excel_path, 
                template_data, 
                mapping_result, 
                healed_data.to_dict()
            )
            
            processing_steps.append({
                "step": 6,
                "name": "Quality Assurance Audit",
                "model": config.grok_model,
                "input_hash": self._get_file_hash(excel_path),
                "output_summary": f"QA Status: {qa_report.get('overall_status')}, Score: {qa_report.get('overall_score', 0)}",
                "latency_seconds": time.time() - step_start,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return qa_report
            
        except Exception as e:
            raise Exception(f"Quality assurance failed: {str(e)}")
    
    def _generate_verification_certificate(self, qa_report: Dict, processing_steps: List[Dict], math_proofs: Dict) -> Dict[str, Any]:
        """Generate verification certificate"""
        step_start = time.time()
        
        try:
            cert_result = self.grok_client.generate_verification_certificate(
                qa_report, 
                processing_steps, 
                math_proofs
            )
            
            # Save certificate to file
            cert_path = os.path.join(config.output_directory, "verification_certificate.html")
            with open(cert_path, 'w', encoding='utf-8') as f:
                f.write(cert_result['certificate_html'])
            
            cert_result['file_path'] = cert_path
            
            return cert_result
            
        except Exception as e:
            raise Exception(f"Certificate generation failed: {str(e)}")
    
    def _update_report_completion(self, report_id: str, healed_data: pd.DataFrame, mapping_result: Dict, qa_report: Dict, cert_data: Dict):
        """Update report record with completion data"""
        try:
            self.db_manager.update_report_completion(
                report_id,
                healed_data.to_dict(),
                mapping_result,
                qa_report,
                cert_data
            )
        except Exception as e:
            print(f"Failed to update report completion: {str(e)}")
    
    def _get_file_hash(self, file_path: str) -> str:
        """Generate SHA256 hash of file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def start_file_monitoring(self, default_user_id: str = "system"):
        """Start automatic file monitoring for zero-touch processing"""
        def monitoring_callback(file_path: str, file_info: Dict):
            """Wrapper callback for file monitoring that adapts signatures"""
            user_id = file_info.get('user_id', default_user_id)
            year = file_info.get('year', 2025)
            self.process_file(file_path, user_id, year)
        
        self.file_monitor.start_monitoring(monitoring_callback)
    
    def stop_file_monitoring(self):
        """Stop file monitoring"""
        self.file_monitor.stop_monitoring()
    
    def get_processing_status(self, report_id: str) -> Dict[str, Any]:
        """Get current processing status for a report"""
        return self.db_manager.get_report_status(report_id)
    
    def get_user_reports(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all reports for a user"""
        return self.db_manager.get_user_reports(user_id)
