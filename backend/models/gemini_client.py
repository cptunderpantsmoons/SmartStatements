"""
Gemini AI Client for PDF Vision Extraction and Data Processing
Handles Google Gemini 2.5 Pro and Flash models
"""
import json
import base64
import hashlib
import time
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import google.generativeai as genai
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import pandas as pd

from ..config.settings import config


class GeminiClient:
    """Client for interacting with Google Gemini AI models"""
    
    def __init__(self):
        """Initialize Gemini client with API key"""
        genai.configure(api_key=config.gemini_api_key)
        self.pro_model = genai.GenerativeModel(config.gemini_pro_model)
        self.flash_model = genai.GenerativeModel(config.gemini_flash_model)
        
    def _get_cache_key(self, prompt: str, content: Any) -> str:
        """Generate cache key for input"""
        content_str = json.dumps(content, sort_keys=True) if isinstance(content, (dict, list)) else str(content)
        combined = f"{prompt}_{content_str}"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def _extract_from_image(self, image_path: str, page_num: int) -> Dict[str, Any]:
        """Extract structured data from a single PDF page image"""
        try:
            # Convert image to base64
            with open(image_path, 'rb') as img_file:
                img_data = img_file.read()
                img_b64 = base64.b64encode(img_data).decode('utf-8')
            
            # Prompt for structured extraction
            prompt = """
            Extract ALL financial data from this PDF page and return as strict JSON:
            {
                "page_number": <page_number>,
                "tables": [
                    {
                        "table_id": <unique_id>,
                        "title": <table_title>,
                        "headers": [<column_headers>],
                        "rows": [[<row_values>]],
                        "position": {"x": <x_coord>, "y": <y_coord>}
                    }
                ],
                "headers": [<page_headers>],
                "footnotes": [<footnote_text>],
                "section_titles": [<section_titles>],
                "formatting": {
                    "fonts": [<font_info>],
                    "colors": [<color_info>],
                    "borders": [<border_info>]
                }
            }
            
            Only return valid JSON. No explanations.
            """
            
            # Call Gemini Pro Vision
            response = self.pro_model.generate_content([
                prompt,
                {
                    "mime_type": "image/jpeg",
                    "data": img_b64
                }
            ])
            
            # Parse response
            try:
                result = json.loads(response.text)
                result["page"] = page_num
                result["extraction_method"] = "gemini_vision"
                return result
            except json.JSONDecodeError:
                # Fallback to OCR if JSON parsing fails
                return self._fallback_ocr_extraction(image_path, page_num)
                
        except Exception as e:
            print(f"Error extracting from page {page_num}: {str(e)}")
            return self._fallback_ocr_extraction(image_path, page_num)
    
    def _fallback_ocr_extraction(self, image_path: str, page_num: int) -> Dict[str, Any]:
        """Fallback OCR extraction using pytesseract"""
        try:
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image)
            
            # Basic text parsing for table-like structures
            lines = text.split('\n')
            tables = []
            current_table = []
            
            for line in lines:
                if line.strip():
                    # Simple heuristic for table rows (contains multiple tabs/spaces)
                    if '\t' in line or '  ' in line:
                        row = [cell.strip() for cell in line.split('\t') if cell.strip()]
                        if len(row) > 1:
                            current_table.append(row)
                    elif current_table:
                        # End of table, save and start new
                        if current_table:
                            tables.append({
                                "table_id": f"ocr_table_{len(tables)}",
                                "title": "Extracted Table",
                                "headers": current_table[0] if current_table else [],
                                "rows": current_table[1:] if len(current_table) > 1 else [],
                                "position": {"x": 0, "y": 0}
                            })
                        current_table = []
            
            # Add last table if exists
            if current_table:
                tables.append({
                    "table_id": f"ocr_table_{len(tables)}",
                    "title": "Extracted Table",
                    "headers": current_table[0] if current_table else [],
                    "rows": current_table[1:] if len(current_table) > 1 else [],
                    "position": {"x": 0, "y": 0}
                })
            
            return {
                "page": page_num,
                "tables": tables,
                "headers": [],
                "footnotes": [],
                "format": {},
                "extraction_method": "ocr_fallback",
                "raw_text": text
            }
            
        except Exception as e:
            print(f"OCR fallback failed for page {page_num}: {str(e)}")
            return {
                "page": page_num,
                "tables": [],
                "headers": [],
                "footnotes": [],
                "format": {},
                "extraction_method": "failed",
                "error": str(e)
            }
    
    def extract_pdf_template(self, pdf_path: str) -> Dict[str, Any]:
        """Extract structured data from 2024 PDF template using parallel processing"""
        start_time = time.time()
        
        try:
            # Convert PDF to images
            images = convert_from_path(pdf_path, dpi=config.pdf_dpi)
            
            # Save images temporarily
            temp_paths = []
            for i, image in enumerate(images):
                temp_path = f"temp_page_{i+1}.jpg"
                image.save(temp_path, 'JPEG')
                temp_paths.append(temp_path)
            
            # Process pages in parallel
            results = []
            with ThreadPoolExecutor(max_workers=config.max_workers) as executor:
                # Submit all tasks
                future_to_page = {
                    executor.submit(self._extract_from_image, temp_path, i+1): i+1
                    for i, temp_path in enumerate(temp_paths)
                }
                
                # Collect results
                for future in as_completed(future_to_page):
                    page_num = future_to_page[future]
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        print(f"Error processing page {page_num}: {str(e)}")
                        results.append({
                            "page": page_num,
                            "tables": [],
                            "headers": [],
                            "footnotes": [],
                            "format": {},
                            "extraction_method": "failed",
                            "error": str(e)
                        })
            
            # Clean up temporary files
            for temp_path in temp_paths:
                try:
                    import os
                    os.remove(temp_path)
                except:
                    pass
            
            # Sort results by page number
            results.sort(key=lambda x: x.get('page', 0))
            
            processing_time = time.time() - start_time
            
            return {
                "source": pdf_path,
                "pages": results,
                "total_pages": len(images),
                "processing_time_seconds": processing_time,
                "extraction_method": "gemini_pro_vision"
            }
            
        except Exception as e:
            raise Exception(f"PDF extraction failed: {str(e)}")
    
    def analyze_data_quality(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Analyze DataFrame for data quality issues using Gemini Flash"""
        start_time = time.time()
        
        try:
            # Prepare data sample for analysis
            data_sample = {
                "columns": df.columns.tolist(),
                "dtypes": df.dtypes.astype(str).to_dict(),
                "sample_data": df.head(20).fillna("").to_dict('records'),
                "null_counts": df.isnull().sum().to_dict(),
                "numeric_stats": df.describe().fillna("").to_dict() if len(df.select_dtypes(include=['number']).columns) > 0 else {}
            }
            
            prompt = """
            Analyze this financial data for quality issues and return JSON:
            {
                "issues": [
                    {
                        "row": <row_index>,
                        "column": <column_name>,
                        "type": "missing|outlier|type_error|inconsistent_format",
                        "severity": "low|medium|high",
                        "description": <detailed_description>,
                        "suggested_value": <suggested_repair_value>,
                        "confidence": <0.0-1.0>
                    }
                ],
                "summary": {
                    "total_issues": <count>,
                    "missing_values": <count>,
                    "outliers": <count>,
                    "type_errors": <count>,
                    "overall_quality_score": <0.0-1.0>
                }
            }
            
            Focus on financial data patterns:
            - Missing values in key financial columns
            - Outliers (>3 standard deviations)
            - Type errors (text in numeric columns)
            - Inconsistent formatting (dates, currency)
            
            Data: {data_sample}
            """.format(data_sample=json.dumps(data_sample, indent=2))
            
            response = self.flash_model.generate_content(prompt)
            
            try:
                result = json.loads(response.text)
                result["analysis_time_seconds"] = time.time() - start_time
                result["model_used"] = config.gemini_flash_model
                return result
            except json.JSONDecodeError:
                # Return basic analysis if JSON parsing fails
                return {
                    "issues": [],
                    "summary": {
                        "total_issues": 0,
                        "missing_values": int(df.isnull().sum().sum()),
                        "outliers": 0,
                        "type_errors": 0,
                        "overall_quality_score": 0.5
                    },
                    "analysis_time_seconds": time.time() - start_time,
                    "model_used": config.gemini_flash_model,
                    "error": "Failed to parse AI response"
                }
                
        except Exception as e:
            raise Exception(f"Data quality analysis failed: {str(e)}")
    
    def generate_excel_code(self, template_data: Dict[str, Any], mapped_data: Dict[str, Any]) -> str:
        """Generate Python code for Excel file creation using Gemini Pro"""
        start_time = time.time()
        
        try:
            prompt = """
            Generate complete Python code using openpyxl to create an Excel file that EXACTLY replicates the 2024 financial statement format with 2025 data.
            
            Requirements:
            - Use openpyxl library
            - Replicate exact formatting: fonts, sizes, colors, borders, column widths, row heights
            - Include conditional formatting, subtotals, grouping, footnotes
            - Match sheet names and order exactly
            - Create pixel-perfect layout matching the template
            
            Template format data: {template_data}
            
            2025 mapped data: {mapped_data}
            
            Return ONLY executable Python code. No explanations, no markdown formatting.
            The code should:
            1. Create a new workbook
            2. Add sheets with exact names
            3. Apply all formatting from template
            4. Fill with 2025 data
            5. Save as '2025_Final.xlsx'
            
            Code:
            """.format(
                template_data=json.dumps(template_data, indent=2),
                mapped_data=json.dumps(mapped_data, indent=2)
            )
            
            response = self.pro_model.generate_content(prompt)
            
            # Clean up response to ensure it's valid Python code
            code = response.text.strip()
            
            # Remove any markdown formatting if present
            if code.startswith('```python'):
                code = code[9:]
            if code.startswith('```'):
                code = code[3:]
            if code.endswith('```'):
                code = code[:-3]
            
            generation_time = time.time() - start_time
            
            return {
                "code": code.strip(),
                "generation_time_seconds": generation_time,
                "model_used": config.gemini_pro_model
            }
            
        except Exception as e:
            raise Exception(f"Excel code generation failed: {str(e)}")
