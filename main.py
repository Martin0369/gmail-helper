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
from dateutil import parser

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
    
    def _check_invoice_exists(self, doc_info, email_info):
        """Check if the invoice has already been processed.
        
        Args:
            doc_info (dict): Document information including extracted invoice details
            email_info (dict): Email information
            
        Returns:
            bool: True if invoice already exists, False otherwise
        """
        try:
            if not doc_info or 'extracted_info' not in doc_info:
                return False
                
            info = doc_info['extracted_info']
            
            # Build search criteria
            search_parts = []
            
            # Add invoice number if available
            invoice_number = info.get('invoice_number', '')
            if invoice_number:
                search_parts.append(f"name contains '{invoice_number}'")
            
            # Add invoice date if available
            invoice_date = info.get('invoice_date', '')
            if invoice_date:
                try:
                    parsed_date = parser.parse(invoice_date)
                    date_str = parsed_date.strftime('%Y%m%d')
                    search_parts.append(f"name contains '{date_str}'")
                except:
                    pass
            
            # Add amount if available
            amount = info.get('amount', '')
            if amount:
                search_parts.append(f"name contains 'NT${amount}'")
            
            if not search_parts:
                return False
            
            # Build query
            query = [
                "mimeType!='application/vnd.google-apps.folder'",
                "trashed=false",
                f"'{config.DRIVE_FOLDER_ID}' in parents",
                "(" + " and ".join(search_parts) + ")"
            ]
            
            # Search in Drive
            results = self.drive_service.service.files().list(
                q=' and '.join(query),
                spaces='drive',
                fields='files(id, name)',
                orderBy='createdTime desc'
            ).execute()
            
            files = results.get('files', [])
            return len(files) > 0
            
        except Exception as e:
            logger.error(f"Error checking invoice existence: {str(e)}")
            return False
    
    def _process_email(self, email):
        """Process a single email and its attachments."""
        try:
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
                
                # Check if invoice already exists
                if doc_info['document_type'] == 'invoice' and self._check_invoice_exists(doc_info, email):
                    logger.info(f"發票已存在，跳過處理: {attachment['filename']}")
                    continue
                
                # Create folder structure based on document type and info
                folder_id = self._create_folder_structure(
                    email,
                    doc_info['document_type'],
                    doc_info
                )
                
                if not folder_id:
                    logger.error(f"無法建立資料夾結構，郵件主旨: {email['subject']}")
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
                        'extracted_info': doc_info.get('extracted_info', {})
                    }
                    
                    self.drive_service.update_file_metadata(
                        drive_file['file_id'],
                        metadata
                    )
                    
                    logger.info(f"成功處理並上傳檔案: {filename}")
                    
        except Exception as e:
            logger.error(f"處理郵件時發生錯誤: {str(e)}")
    
    def _create_folder_structure(self, email_info, doc_type, doc_info=None):
        """Create folder structure based on email information and document type.
        
        For invoices, the folder structure will be:
        Year/Month/Vendor/InvoiceDate_Description/
        """
        try:
            # Parse email date for year/month folders
            email_date = self._parse_date(email_info['date'])
            if not email_date:
                return None
            
            year = str(email_date.year)
            month = f"{email_date.month:02d}"
            
            # Create year and month folders
            year_folder = self.drive_service.get_or_create_folder(year)
            if not year_folder:
                logger.error(f"無法建立年份資料夾: {year}")
                return None
                
            month_folder = self.drive_service.get_or_create_folder(month, parent_folder_id=year_folder)
            if not month_folder:
                logger.error(f"無法建立月份資料夾: {month}")
                return None
            
            if doc_type == 'invoice' and doc_info and 'extracted_info' in doc_info:
                info = doc_info['extracted_info']
                
                # Get vendor name
                vendor = info.get('seller_name', '')
                if not vendor:
                    # 如果沒有賣家名稱，使用郵件主旨中的公司名稱
                    subject = email_info.get('subject', '')
                    if '電子發票' in subject or '發票' in subject:
                        # 嘗試從主旨中提取公司名稱
                        vendor = subject.split('：')[0] if '：' in subject else subject.split(':')[0]
                    else:
                        # 如果還是無法獲取，使用寄件者信箱
                        vendor = email_info.get('from', '').split('@')[0]
                
                vendor = self._clean_folder_name(vendor)
                if not vendor:
                    logger.error("無法獲取有效的供應商名稱")
                    return month_folder
                
                vendor_folder = self.drive_service.get_or_create_folder(vendor, parent_folder_id=month_folder)
                if not vendor_folder:
                    logger.error(f"無法建立供應商資料夾: {vendor}")
                    return month_folder
                
                # Get invoice date and create description
                invoice_date = info.get('invoice_date', '')
                if invoice_date:
                    try:
                        # Parse invoice date
                        parsed_date = parser.parse(invoice_date)
                        invoice_date_str = parsed_date.strftime('%Y%m%d')
                        
                        # Create description from invoice details
                        description_parts = []
                        
                        # Add invoice number if available
                        invoice_number = info.get('invoice_number', '')
                        if invoice_number:
                            description_parts.append(invoice_number)
                        
                        # Add amount if available
                        amount = info.get('amount', '')
                        if amount:
                            description_parts.append(f'NT${amount}')
                        
                        # Add tax ID if available
                        tax_id = info.get('tax_id', '')
                        if tax_id:
                            description_parts.append(f'統編{tax_id}')
                        
                        # Create folder name with date and description
                        folder_name = invoice_date_str
                        if description_parts:
                            folder_name += '_' + '_'.join(description_parts)
                        
                        folder_name = self._clean_folder_name(folder_name)
                        invoice_folder = self.drive_service.get_or_create_folder(folder_name, parent_folder_id=vendor_folder)
                        if invoice_folder:
                            return invoice_folder
                        else:
                            logger.error(f"無法建立發票資料夾: {folder_name}")
                            return vendor_folder
                        
                    except Exception as e:
                        logger.error(f"處理發票日期時發生錯誤: {str(e)}")
                        return vendor_folder
                
                return vendor_folder
            else:
                # For non-invoice documents
                sender = email_info.get('from', '').split('@')[0]
                sender = self._clean_folder_name(sender)
                if not sender:
                    sender = "unknown_sender"
                
                sender_folder = self.drive_service.get_or_create_folder(sender, parent_folder_id=month_folder)
                if not sender_folder:
                    logger.error(f"無法建立寄件者資料夾: {sender}")
                    return month_folder
                
                # Create a more descriptive folder name from subject and date
                subject = email_info.get('subject', '')
                if subject:
                    # Clean and format subject
                    clean_subject = self._clean_folder_name(subject)
                    
                    # Add date to subject if available
                    if email_date:
                        date_str = email_date.strftime('%Y%m%d')
                        folder_name = f"{date_str}_{clean_subject}"
                    else:
                        folder_name = clean_subject
                    
                    # Limit length
                    if len(folder_name) > 100:
                        folder_name = folder_name[:97] + '...'
                    
                    subject_folder = self.drive_service.get_or_create_folder(folder_name, parent_folder_id=sender_folder)
                    if subject_folder:
                        return subject_folder
                    else:
                        logger.error(f"無法建立主旨資料夾: {folder_name}")
                        return sender_folder
                
                return sender_folder
                
        except Exception as e:
            logger.error(f"建立資料夾結構時發生錯誤: {str(e)}")
            return None
    
    def _clean_folder_name(self, name):
        """Clean folder name to be compatible with file system.
        
        Args:
            name (str): Original folder name
            
        Returns:
            str: Cleaned folder name
        """
        if not name:
            return ''
            
        # Replace invalid characters with underscore
        invalid_chars = r'[<>:"/\\|?*]'
        name = re.sub(invalid_chars, '_', name)
        
        # Remove leading/trailing spaces and dots
        name = name.strip('. ')
        
        # Limit length to 255 characters
        if len(name) > 255:
            name = name[:255]
            
        # Use default name if empty after cleaning
        if not name:
            name = 'unnamed'
            
        return name
    
    def _generate_filename(self, doc_type, original_filename, sender, doc_info=None):
        """Generate a standardized filename based on document type and information.
        
        Args:
            doc_type (str): Type of document (e.g., 'invoice', 'receipt')
            original_filename (str): Original filename from email
            sender (str): Email sender
            doc_info (dict): Additional document information
            
        Returns:
            str: Generated filename
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if doc_type == 'invoice' and doc_info:
            # Extract invoice information
            date = doc_info.get('date', '')
            if date:
                try:
                    date = parser.parse(date).strftime('%Y%m%d')
                except:
                    date = ''
            
            vendor = doc_info.get('seller', '')
            invoice_number = doc_info.get('invoice_number', '')
            amount = doc_info.get('amount', '')
            
            # Build filename components
            components = []
            if date:
                components.append(date)
            if vendor:
                components.append(self._clean_folder_name(vendor))
            if invoice_number:
                components.append(invoice_number)
            if amount:
                components.append(f'{amount}元')
                
            # Add timestamp if no components
            if not components:
                components.append(timestamp)
                
            filename = '_'.join(components)
        else:
            # For non-invoice documents
            sender = self._clean_folder_name(sender)
            base_name = os.path.splitext(original_filename)[0]
            filename = f'{sender}_{base_name}_{timestamp}'
            
        # Get original extension or default to .pdf
        ext = os.path.splitext(original_filename)[1].lower()
        if not ext:
            ext = '.pdf'
            
        # Clean and return full filename
        filename = self._clean_folder_name(filename)
        return f'{filename}{ext}'
    
    def _parse_date(self, date_str):
        """Parse date string with multiple format support.
        
        Args:
            date_str (str): Date string to parse
            
        Returns:
            datetime: Parsed datetime object or None if parsing fails
        """
        try:
            # Remove timezone name (UTC, CST, etc.)
            date_str = re.sub(r'\s*\([A-Z]{2,}\)', '', date_str)
            
            # Try parsing with dateutil first
            try:
                return parser.parse(date_str)
            except:
                pass
                
            # Try specific formats
            formats = [
                '%a, %d %b %Y %H:%M:%S %z',  # RFC 2822
                '%Y-%m-%d %H:%M:%S%z',       # ISO format
                '%Y年%m月%d日',              # Chinese format
                '%Y/%m/%d',                  # Simple date
                '%Y%m%d'                     # Compact date
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except:
                    continue
                    
            return None
            
        except Exception as e:
            logger.error(f"日期解析錯誤: {str(e)}, 日期字串: {date_str}")
            return None

def main():
    processor = GmailAttachmentProcessor()
    processor.process_emails()

if __name__ == "__main__":
    main() 