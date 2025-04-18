import os
import logging

# Google Cloud 設定
GOOGLE_APPLICATION_CREDENTIALS = os.path.join(os.path.dirname(__file__), 'credentials.json')

# Gmail API 設定
GMAIL_QUERY = 'has:attachment -label:processed'  # Gmail 搜尋條件
GMAIL_LABEL = 'processed'  # 處理完成後的標籤

# Google Drive 設定
DRIVE_ROOT_FOLDER = 'Gmail附件'  # Google Drive 根資料夾名稱

# 文件類型關鍵字
DOCUMENT_KEYWORDS = {
    'invoice': ['發票', '統一發票', 'invoice', '電子發票'],
    'quotation': ['報價', '報價單', 'quotation'],
    'contract': ['合約', '契約', 'contract', 'agreement'],
    'receipt': ['收據', '收條', 'receipt'],
    'order': ['訂單', '訂購單', 'order', 'purchase order']
}

# 日誌設定
LOG_FILE = 'gmail_helper.log'
LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5

# OCR 設定
OCR_LANGUAGE_HINTS = ['zh-TW', 'en']  # OCR 語言提示

# 檔案處理設定
MAX_FILE_SIZE = 10 * 1024 * 1024  # 最大檔案大小 (10MB)
SUPPORTED_MIME_TYPES = [
    'application/pdf',
    'image/jpeg',
    'image/png',
    'image/tiff',
    'image/bmp'
]

# 重試設定
MAX_RETRIES = 3  # 最大重試次數
RETRY_DELAY = 5  # 重試延遲（秒） 