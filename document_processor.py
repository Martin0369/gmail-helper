import os
import io
import json
import re
from datetime import datetime
from google.cloud import vision
import fitz  # PyMuPDF
from pdf2image import convert_from_bytes
import spacy
import config

class DocumentProcessor:
    def __init__(self):
        # Initialize Vision client with explicit credentials
        try:
            credentials_path = os.path.normpath(config.GOOGLE_APPLICATION_CREDENTIALS)
            if not os.path.exists(credentials_path):
                raise FileNotFoundError(f"Credentials file not found at: {credentials_path}")
                
            self.vision_client = vision.ImageAnnotatorClient.from_service_account_json(
                credentials_path
            )
            print(f"Successfully initialized Vision client with credentials from: {credentials_path}")
        except Exception as e:
            print(f"Error initializing Vision client: {str(e)}")
            raise
            
        try:
            self.nlp = spacy.load("zh_core_web_sm")
        except Exception as e:
            print(f"Error loading spaCy model: {str(e)}")
            raise
            
        # Set up Poppler path for Windows
        if os.name == 'nt':  # Windows
            poppler_path = os.path.join(os.environ.get('PROGRAMFILES', 'C:\\Program Files'), 'poppler', 'Library', 'bin')
            if os.path.exists(poppler_path):
                os.environ['PATH'] = poppler_path + os.pathsep + os.environ.get('PATH', '')
            else:
                print(f"Warning: Poppler not found at {poppler_path}")
                print("Please install Poppler and add it to PATH")
        
    def process_document(self, file_data, mime_type):
        """Process document and extract information."""
        try:
            # Convert PDF to images if necessary
            if mime_type == 'application/pdf':
                images = self._pdf_to_images(file_data)
            else:
                images = [file_data]
            
            # Process each image
            extracted_text = []
            for image_data in images:
                text = self._perform_ocr(image_data)
                if text:
                    extracted_text.append(text)
            
            # Combine all extracted text
            full_text = '\n'.join(extracted_text)
            
            # Analyze document type and extract information
            doc_type = self._classify_document(full_text)
            extracted_info = self._extract_information(full_text, doc_type)
            
            return {
                'document_type': doc_type,
                'extracted_text': full_text,
                'extracted_info': extracted_info,
                'processed_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error processing document: {str(e)}")
            return None
    
    def _pdf_to_images(self, pdf_data):
        """Convert PDF to images."""
        try:
            # Try using pdf2image with explicit poppler path
            if os.name == 'nt':  # Windows
                poppler_path = os.path.join(os.environ.get('PROGRAMFILES', 'C:\\Program Files'), 'poppler', 'Library', 'bin')
                images = convert_from_bytes(pdf_data, poppler_path=poppler_path)
            else:
                images = convert_from_bytes(pdf_data)
                
            image_data = []
            for image in images:
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format='PNG')
                image_data.append(img_byte_arr.getvalue())
            return image_data
            
        except Exception as e:
            print(f"Error converting PDF to images: {str(e)}")
            print("If Poppler is not installed, please install it from: https://github.com/oschwartz10612/poppler-windows/releases/")
            # Fallback to PyMuPDF
            try:
                print("Attempting to use PyMuPDF as fallback...")
                pdf_doc = fitz.open(stream=pdf_data, filetype="pdf")
                image_data = []
                for page in pdf_doc:
                    pix = page.get_pixmap()
                    img_data = pix.tobytes()
                    image_data.append(img_data)
                return image_data
            except Exception as fallback_e:
                print(f"Fallback to PyMuPDF also failed: {str(fallback_e)}")
                return []
    
    def _perform_ocr(self, image_data):
        """Perform OCR on image using Google Cloud Vision."""
        try:
            image = vision.Image(content=image_data)
            response = self.vision_client.text_detection(image=image)
            texts = response.text_annotations
            
            if texts:
                return texts[0].description
            return ''
            
        except Exception as e:
            print(f"Error performing OCR: {str(e)}")
            return ''
    
    def _classify_document(self, text):
        """Classify document type based on content."""
        text_lower = text.lower()
        
        # Check for invoice keywords first
        invoice_keywords = ['發票', '統一發票', 'invoice', '電子發票']
        for keyword in invoice_keywords:
            if keyword.lower() in text_lower:
                return 'invoice'
        
        # Then check other document types
        for doc_type, keywords in config.DOCUMENT_KEYWORDS.items():
            if any(keyword.lower() in text_lower for keyword in keywords):
                return doc_type
                
        return 'unknown'
    
    def _extract_information(self, text, doc_type):
        """Extract relevant information based on document type."""
        doc = self.nlp(text)
        info = {}
        
        if doc_type == 'invoice':
            info = self._extract_invoice_info(text, doc)
        elif doc_type == 'quotation':
            info = self._extract_quotation_info(doc)
        elif doc_type == 'contract':
            info = self._extract_contract_info(doc)
            
        return info
    
    def _extract_invoice_info(self, text, doc):
        """Extract information from invoice."""
        info = {
            'invoice_number': '',
            'invoice_date': '',
            'buyer': '',
            'seller': '',
            'amount': '',
            'tax_id': ''
        }
        
        # Extract invoice number (統一發票號碼格式: XX-XXXXXXXX)
        invoice_number_pattern = r'[A-Z]{2}[-]?\d{8}'
        invoice_matches = re.findall(invoice_number_pattern, text)
        if invoice_matches:
            info['invoice_number'] = invoice_matches[0].replace('-', '')
            
        # Extract date (支援多種日期格式)
        date_patterns = [
            r'(\d{4})[年/\-](\d{1,2})[月/\-](\d{1,2})',  # 2024年03月15日
            r'(\d{3})[年/\-](\d{1,2})[月/\-](\d{1,2})',   # 民國113年03月15日
            r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})',      # 03/15/2024
        ]
        
        for pattern in date_patterns:
            date_matches = re.findall(pattern, text)
            if date_matches:
                year, month, day = date_matches[0]
                # 處理民國年
                if len(year) == 3:
                    year = str(int(year) + 1911)
                info['invoice_date'] = f"{year}-{month:0>2}-{day:0>2}"
                break
                
        # Extract tax ID (統一編號格式: 8位數字)
        tax_id_pattern = r'統一編號[：: ]*(\d{8})'
        tax_id_matches = re.findall(tax_id_pattern, text)
        if tax_id_matches:
            info['tax_id'] = tax_id_matches[0]
            
        # Extract seller and buyer
        company_patterns = [
            r'公司名稱[：: ]*([^\n]+)',
            r'買受人[：: ]*([^\n]+)',
            r'賣方[：: ]*([^\n]+)',
            r'商店名稱[：: ]*([^\n]+)'
        ]
        
        companies = []
        for pattern in company_patterns:
            matches = re.findall(pattern, text)
            companies.extend(matches)
            
        # Also use spaCy NER to find organization names
        for ent in doc.ents:
            if ent.label_ == 'ORG':
                companies.append(ent.text)
                
        # Remove duplicates and assign roles
        companies = list(dict.fromkeys(companies))
        if companies:
            info['seller'] = companies[0]
            if len(companies) > 1:
                info['buyer'] = companies[1]
                
        # Extract amount
        amount_patterns = [
            r'總計[：: ]*NT?\$?(\d+[,\d]*\d*)',
            r'總額[：: ]*NT?\$?(\d+[,\d]*\d*)',
            r'金額[：: ]*NT?\$?(\d+[,\d]*\d*)'
        ]
        
        for pattern in amount_patterns:
            amount_matches = re.findall(pattern, text)
            if amount_matches:
                info['amount'] = amount_matches[0].replace(',', '')
                break
                
        return info
    
    def _extract_quotation_info(self, doc):
        """Extract information from quotation."""
        info = {
            'quotation_number': '',
            'quotation_date': '',
            'company': '',
            'total_amount': ''
        }
        return info
    
    def _extract_contract_info(self, doc):
        """Extract information from contract."""
        info = {
            'contract_number': '',
            'contract_date': '',
            'parties': [],
            'contract_value': ''
        }
        return info 