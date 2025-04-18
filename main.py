import os
import json
import logging
from datetime import datetime
import email.utils
import re
from gmail_service import GmailService
from drive_service import DriveService
from document_processor import DocumentProcessor
import config

# Set up logging with UTF-8 encoding
logging.basicConfig(
    filename=config.LOG_FILE,
    level=config.LOG_LEVEL,
    format=config.LOG_FORMAT,
    encoding='utf-8'
)
logger = logging.getLogger(__name__)

class GmailAttachmentProcessor:
    def __init__(self):
        self.gmail_service = GmailService()
        self.drive_service = DriveService()
        self.doc_processor = DocumentProcessor()
        
    def process_emails(self):
        """Main process to handle email attachments."""
        try:
            # Get emails with attachments
            emails = self.gmail_service.get_emails_with_attachments()
            logger.info(f"找到 {len(emails)} 封含附件的郵件")
            
            for email in emails:
                self._process_email(email)
                
        except Exception as e:
            logger.error(f"主程序執行錯誤: {str(e)}")
    
    def _process_email(self, email):
        """Process a single email and its attachments."""
        try:
            # Create folder structure based on email information
            folder_id = self._create_folder_structure(email)
            if not folder_id:
                logger.error(f"無法建立資料夾結構，郵件主旨: {email['subject']}")
                return
                
            for attachment in email['attachments']:
                # Download attachment
                file_data = self.gmail_service.download_attachment(
                    email['message_id'],
                    attachment['id']
                )
                
                if not file_data:
                    logger.warning(f"無法下載附件: {attachment['filename']}")
                    continue
                
                # Process document
                doc_info = self.doc_processor.process_document(
                    file_data,
                    attachment['mimeType']
                )
                
                if not doc_info:
                    logger.warning(f"無法處理文件: {attachment['filename']}")
                    continue
                
                # Generate filename
                filename = self._generate_filename(
                    doc_info['document_type'],
                    attachment['filename'],
                    email['sender'],
                    doc_info
                )
                
                # Upload to Drive
                drive_file = self.drive_service.upload_file(
                    file_data,
                    filename,
                    attachment['mimeType'],
                    folder_id
                )
                
                if drive_file:
                    # Update metadata
                    metadata = {
                        'document_type': doc_info['document_type'],
                        'processed_date': doc_info['processed_date'],
                        'source_email': email['sender'],
                        'extracted_info': doc_info['extracted_info']
                    }
                    
                    self.drive_service.update_file_metadata(
                        drive_file['file_id'],
                        metadata
                    )
                    
                    logger.info(f"成功處理並上傳檔案: {filename}")
                    
        except Exception as e:
            logger.error(f"處理郵件時發生錯誤: {str(e)}")
    
    def _create_folder_structure(self, email):
        """Create folder structure based on email information."""
        try:
            # Parse email date with multiple formats
            email_date = None
            date_str = email['date']
            
            # Try different date formats
            date_formats = [
                '%a, %d %b %Y %H:%M:%S %z',  # Standard format
                '%d %b %Y %H:%M:%S %z',      # Without weekday
                '%Y-%m-%d %H:%M:%S %z',      # ISO format
                '%Y/%m/%d %H:%M:%S %z'       # Common format
            ]
            
            for date_format in date_formats:
                try:
                    # Remove any extra timezone info in parentheses
                    cleaned_date = re.sub(r'\([^)]*\)', '', date_str).strip()
                    email_date = datetime.strptime(cleaned_date, date_format)
                    break
                except ValueError:
                    continue
            
            if not email_date:
                # If all formats fail, try parsing with email.utils
                try:
                    email_date = datetime(*email.utils.parsedate_tz(date_str)[:6])
                except:
                    # If all parsing attempts fail, use current time
                    email_date = datetime.now()
                    logger.warning(f"無法解析日期 '{date_str}'，使用當前時間")
            
            year_month = email_date.strftime('%Y_%m')
            
            # Extract sender domain and name
            sender_parts = email['sender'].split('@')
            sender_name = sender_parts[0].strip('"<>')
            sender_domain = sender_parts[1].strip('>"') if len(sender_parts) > 1 else 'unknown'
            
            # Create year_month folder
            year_month_folder_id = self.drive_service.get_or_create_folder(year_month)
            if not year_month_folder_id:
                return None
                
            # Create sender folder (use sender name instead of domain)
            sender_folder_id = self.drive_service.get_or_create_folder(
                sender_name,
                year_month_folder_id
            )
            if not sender_folder_id:
                return None
                
            # Create subject folder (cleaned)
            subject_folder = self._clean_folder_name(email['subject'])
            if not subject_folder:
                subject_folder = 'No_Subject'
                
            email_folder_id = self.drive_service.get_or_create_folder(
                subject_folder,
                sender_folder_id
            )
            
            return email_folder_id
            
        except Exception as e:
            logger.error(f"建立資料夾結構時發生錯誤: {str(e)}")
            return None
    
    def _clean_folder_name(self, name):
        """Clean folder name to be compatible with Google Drive."""
        if not name:
            return 'No_Name'
            
        # Remove invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
            
        # Remove control characters
        name = ''.join(char for char in name if ord(char) >= 32)
        
        # Limit length
        if len(name) > 100:
            name = name[:97] + '...'
            
        # Remove leading/trailing spaces and dots
        name = name.strip('. ')
        
        return name if name else 'No_Name'
    
    def _generate_filename(self, doc_type, original_filename, sender, doc_info=None):
        """Generate a standardized filename."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Clean sender name
        sender_name = sender.split('@')[0].strip('"<>')
        sender_name = self._clean_folder_name(sender_name)
        
        # Get file extension
        _, ext = os.path.splitext(original_filename)
        if not ext:
            ext = '.unknown'
        
        # Clean document type
        doc_type = doc_type.replace(' ', '_').lower()
        
        # For invoices, include additional information
        if doc_type == 'invoice' and doc_info and isinstance(doc_info, dict):
            extracted_info = doc_info.get('extracted_info', {})
            if extracted_info:
                invoice_date = extracted_info.get('invoice_date', '')
                invoice_number = extracted_info.get('invoice_number', '')
                seller = extracted_info.get('seller', '')
                
                # Clean seller name
                if seller:
                    seller = self._clean_folder_name(seller)
                    seller = seller[:30]  # Limit length
                
                # Format invoice date
                if invoice_date:
                    invoice_date = invoice_date.replace('-', '')
                else:
                    invoice_date = timestamp[:8]  # Use current date if not available
                
                # Create filename with invoice details
                if invoice_number and seller:
                    return f"invoice_{invoice_date}_{seller}_{invoice_number}{ext}"
                elif invoice_number:
                    return f"invoice_{invoice_date}_{invoice_number}{ext}"
                elif seller:
                    return f"invoice_{invoice_date}_{seller}{ext}"
        
        # Default filename format for non-invoices or when invoice info is not available
        return f"{doc_type}_{timestamp}_{sender_name}{ext}"

def main():
    processor = GmailAttachmentProcessor()
    processor.process_emails()

if __name__ == "__main__":
    main() 