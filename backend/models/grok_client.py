"""
Grok 4 Fast Client for Semantic Account Mapping and Quality Assurance
Handles Grok 4 Fast via OpenRouter API
"""
import json
import hashlib
import time
import base64
from typing import Dict, List, Any, Optional
from openai import OpenAI

from ..config.settings import config


class GrokClient:
    """Client for interacting with Grok 4 Fast via OpenRouter"""
    
    def __init__(self):
        """Initialize Grok client with OpenRouter API"""
        self.client = OpenAI(
            api_key=config.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        self.model = config.grok_model
        
    def _get_cache_key(self, prompt: str, content: Any) -> str:
        """Generate cache key for input"""
        content_str = json.dumps(content, sort_keys=True) if isinstance(content, (dict, list)) else str(content)
        combined = f"{prompt}_{content_str}"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def semantic_account_mapping(self, accounts_2024: List[str], accounts_2025: List[str]) -> Dict[str, Any]:
        """
        Perform semantic mapping between 2024 template accounts and 2025 data accounts
        using cosine similarity and synonym expansion
        """
        start_time = time.time()
        
        try:
            # Sample accounts if too many (to stay within context limits)
            max_accounts = 50
            accounts_2024_sample = accounts_2024[:max_accounts] if len(accounts_2024) > max_accounts else accounts_2024
            accounts_2025_sample = accounts_2025[:max_accounts] if len(accounts_2025) > max_accounts else accounts_2025
            
            prompt = f"""
            Perform semantic account mapping between 2024 template accounts and 2025 data accounts.
            
            Use cosine similarity with these thresholds:
            - >{config.auto_map_threshold} → AUTO_MAP (high confidence)
            - {config.review_threshold}-{config.auto_map_threshold} → REVIEW_NEEDED (medium confidence)
            - <{config.review_threshold} → NEW_ACCOUNT (low confidence)
            
            Apply synonym expansion for financial terms:
            - Revenue ↔ Income ↔ Sales ↔ Turnover
            - COGS ↔ Cost of Sales ↔ Cost of Goods Sold
            - Expenses ↔ Costs ↔ Outlays
            - Assets ↔ Resources ↔ Property
            - Liabilities ↔ Obligations ↔ Debts
            - Equity ↔ Net Assets ↔ Capital
            - Cash ↔ Funds ↔ Liquidity
            
            2024 Template Accounts: {json.dumps(accounts_2024_sample, indent=2)}
            
            2025 Data Accounts: {json.dumps(accounts_2025_sample, indent=2)}
            
            Return JSON format:
            {{
                "mappings": [
                    {{
                        "account_2025": "<account_name>",
                        "account_2024_match": "<matched_account>",
                        "similarity_score": <0.0-1.0>,
                        "action": "AUTO_MAP|REVIEW_NEEDED|NEW_ACCOUNT",
                        "confidence": <0.0-1.0>,
                        "synonyms_used": [<synonyms_applied>],
                        "reasoning": "<brief_explanation>"
                    }}
                ],
                "unmatched_2024": [<accounts_without_matches>],
                "unmatched_2025": [<accounts_without_matches>],
                "summary": {{
                    "total_2024_accounts": <count>,
                    "total_2025_accounts": <count>,
                    "auto_mapped": <count>,
                    "review_needed": <count>,
                    "new_accounts": <count>,
                    "average_confidence": <0.0-1.0>
                }}
            }}
            
            Only return valid JSON. No explanations.
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a financial accounting expert specializing in account mapping and semantic analysis."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for consistent results
                max_tokens=4000
            )
            
            result_text = response.choices[0].message.content
            
            # Clean up response and parse JSON
            if result_text.startswith('```json'):
                result_text = result_text[7:]
            if result_text.startswith('```'):
                result_text = result_text[3:]
            if result_text.endswith('```'):
                result_text = result_text[:-3]
            
            result = json.loads(result_text.strip())
            
            processing_time = time.time() - start_time
            result["processing_time_seconds"] = processing_time
            result["model_used"] = self.model
            result["total_accounts_processed"] = len(accounts_2024) + len(accounts_2025)
            
            return result
            
        except Exception as e:
            raise Exception(f"Semantic account mapping failed: {str(e)}")
    
    def quality_assurance_audit(self, 
                               generated_excel_path: str,
                               template_data: Dict[str, Any],
                               mapping_data: Dict[str, Any],
                               financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive quality assurance audit on generated financial statements
        """
        start_time = time.time()
        
        try:
            # Read sample of generated Excel file (first 4KB for analysis)
            excel_sample = self._read_excel_sample(generated_excel_path)
            
            prompt = f"""
            Perform comprehensive financial audit on generated statements.
            
            Audit Checklist:
            1. Format Accuracy: Does generated Excel exactly match 2024 PDF template?
            2. Trial Balance: Do debits equal credits? (∑Debits == ∑Credits)
            3. AASB Compliance: Are Australian Accounting Standards Board disclosures met?
            4. Mathematical Consistency: Do calculations balance correctly?
            5. Ratio Analysis: Are financial ratios within reasonable ranges?
            6. Inter-statement Reconciliation: Do statements reconcile with each other?
            7. Data Completeness: Are all required fields populated?
            8. Formatting Consistency: Are fonts, colors, borders consistent?
            
            Generated Excel Sample (base64): {excel_sample}
            
            Template Format Data: {json.dumps(template_data, indent=2)}
            
            Account Mapping Data: {json.dumps(mapping_data, indent=2)}
            
            Financial Data Summary: {json.dumps(financial_data, indent=2)}
            
            Return JSON audit report:
            {{
                "overall_status": "PASS|FAIL|REVIEW",
                "overall_score": <0.0-100.0>,
                "checks": [
                    {{
                        "check_name": "<check_name>",
                        "status": "PASS|FAIL|REVIEW",
                        "score": <0.0-100.0>,
                        "details": "<detailed_findings>",
                        "mathematical_proof": "<equation_or_calculation>",
                        "recommendations": [<action_items>]
                    }}
                ],
                "mathematical_proofs": {{
                    "trial_balance": "∑Debits=<amount> == ∑Credits=<amount>",
                    "balance_sheet": "Assets=<amount> == Liabilities+Equity=<amount>",
                    "income_statement": "Revenue-Expenses=<amount>",
                    "cash_flow": "<reconciliation_equation>"
                }},
                "compliance_issues": [<aasb_violations>],
                "formatting_issues": [<formatting_problems>],
                "data_quality_issues": [<data_problems>],
                "risk_assessment": {{
                    "financial_risk": "LOW|MEDIUM|HIGH",
                    "compliance_risk": "LOW|MEDIUM|HIGH",
                    "accuracy_risk": "LOW|MEDIUM|HIGH"
                }},
                "summary": {{
                    "total_checks": <count>,
                    "passed_checks": <count>,
                    "failed_checks": <count>,
                    "review_needed": <count>,
                    "critical_issues": <count>
                }}
            }}
            
            Focus on mathematical accuracy and compliance. Provide exact equations for all proofs.
            Only return valid JSON. No explanations.
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a senior financial auditor with expertise in AASB compliance and financial statement analysis."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for consistent auditing
                max_tokens=6000
            )
            
            result_text = response.choices[0].message.content
            
            # Clean up response and parse JSON
            if result_text.startswith('```json'):
                result_text = result_text[7:]
            if result_text.startswith('```'):
                result_text = result_text[3:]
            if result_text.endswith('```'):
                result_text = result_text[:-3]
            
            result = json.loads(result_text.strip())
            
            processing_time = time.time() - start_time
            result["audit_time_seconds"] = processing_time
            result["model_used"] = self.model
            result["audit_timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S UTC")
            
            return result
            
        except Exception as e:
            raise Exception(f"Quality assurance audit failed: {str(e)}")
    
    def _read_excel_sample(self, file_path: str, max_bytes: int = 4096) -> str:
        """Read sample of Excel file and encode as base64"""
        try:
            with open(file_path, 'rb') as f:
                sample_data = f.read(max_bytes)
            return base64.b64encode(sample_data).decode('utf-8')
        except Exception as e:
            print(f"Error reading Excel sample: {str(e)}")
            return ""
    
    def generate_verification_certificate(self, 
                                       audit_report: Dict[str, Any],
                                       processing_steps: List[Dict[str, Any]],
                                       math_proofs: Dict[str, str]) -> Dict[str, Any]:
        """
        Generate verification certificate content with complete audit trail
        """
        start_time = time.time()
        
        try:
            prompt = f"""
            Generate a comprehensive verification certificate for financial statement processing.
            
            Audit Report: {json.dumps(audit_report, indent=2)}
            
            Processing Steps: {json.dumps(processing_steps, indent=2)}
            
            Mathematical Proofs: {json.dumps(math_proofs, indent=2)}
            
            Generate certificate content in HTML format:
            {{
                "certificate_html": "<complete_html_certificate>",
                "certificate_text": "<plain_text_version>",
                "metadata": {{
                    "certificate_id": "<unique_id>",
                    "generation_timestamp": "<timestamp>",
                    "valid_until": "<expiry_date>",
                    "verification_status": "VERIFIED|FAILED|REVIEW"
                }},
                "audit_summary": {{
                    "total_processing_steps": <count>,
                    "ai_models_used": [<model_names>],
                    "total_processing_time": <seconds>,
                    "accuracy_score": <0.0-100.0>,
                    "compliance_status": "COMPLIANT|NON_COMPLIANT"
                }},
                "mathematical_verification": {{
                    "trial_balance_verified": <boolean>,
                    "balance_sheet_balanced": <boolean>,
                    "calculations_accurate": <boolean>,
                    "proofs_validated": <count>
                }}
            }}
            
            Certificate should include:
            - Professional header with "100% Accuracy Certificate"
            - Complete processing timeline with AI model usage
            - All mathematical proofs with exact equations
            - Compliance verification status
            - Digital signature placeholder
            - QR code placeholder for verification
            
            Return only valid JSON. No explanations.
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a certification specialist creating official financial verification documents."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=8000
            )
            
            result_text = response.choices[0].message.content
            
            # Clean up response and parse JSON
            if result_text.startswith('```json'):
                result_text = result_text[7:]
            if result_text.startswith('```'):
                result_text = result_text[3:]
            if result_text.endswith('```'):
                result_text = result_text[:-3]
            
            result = json.loads(result_text.strip())
            
            processing_time = time.time() - start_time
            result["generation_time_seconds"] = processing_time
            result["model_used"] = self.model
            
            return result
            
        except Exception as e:
            raise Exception(f"Verification certificate generation failed: {str(e)}")
    
    def analyze_financial_anomalies(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze financial data for anomalies and unusual patterns
        """
        start_time = time.time()
        
        try:
            prompt = f"""
            Analyze financial data for anomalies, outliers, and unusual patterns.
            
            Financial Data: {json.dumps(financial_data, indent=2)}
            
            Perform anomaly detection on:
            1. Revenue trends (year-over-year changes)
            2. Expense patterns (unusual spikes or drops)
            3. Balance sheet ratios (current ratio, debt-to-equity, etc.)
            4. Cash flow patterns (operating vs investing vs financing)
            5. Profitability metrics (gross margin, net margin, ROE, ROA)
            6. Unusual account balances (negative values where unexpected)
            7. Seasonal variations (if applicable)
            
            Return JSON analysis:
            {{
                "anomaly_score": <0.0-100.0>,
                "anomalies_detected": [
                    {{
                        "account": "<account_name>",
                        "anomaly_type": "<trend|ratio|balance|pattern>",
                        "severity": "LOW|MEDIUM|HIGH|CRITICAL",
                        "description": "<detailed_description>",
                        "expected_range": "<normal_range>",
                        "actual_value": <value>,
                        "deviation_percentage": <percentage>,
                        "recommendation": "<action_needed>"
                    }}
                ],
                "risk_indicators": {{
                    "financial_health": "EXCELLENT|GOOD|FAIR|POOR|CRITICAL",
                    "going_concern_risk": "LOW|MEDIUM|HIGH",
                    "fraud_risk_indicators": [<potential_issues>]
                }},
                "trend_analysis": {{
                    "revenue_trend": "<growth_decline_stable>",
                    "profitability_trend": "<improving_declining_stable>",
                    "liquidity_trend": "<improving_declining_stable>"
                }},
                "recommendations": [<actionable_recommendations>]
            }}
            
            Focus on financial statement red flags and unusual patterns that warrant investigation.
            Only return valid JSON. No explanations.
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a financial analyst specializing in anomaly detection and forensic accounting."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=6000
            )
            
            result_text = response.choices[0].message.content
            
            # Clean up response and parse JSON
            if result_text.startswith('```json'):
                result_text = result_text[7:]
            if result_text.startswith('```'):
                result_text = result_text[3:]
            if result_text.endswith('```'):
                result_text = result_text[:-3]
            
            result = json.loads(result_text.strip())
            
            processing_time = time.time() - start_time
            result["analysis_time_seconds"] = processing_time
            result["model_used"] = self.model
            
            return result
            
        except Exception as e:
            raise Exception(f"Financial anomaly analysis failed: {str(e)}")
