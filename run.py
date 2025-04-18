#!/usr/bin/env python3
import os
import sys
import logging
from logging.handlers import RotatingFileHandler
import traceback
from main import GmailAttachmentProcessor
import config

def setup_logging():
    """設置日誌系統"""
    # 建立日誌目錄
    log_dir = os.path.dirname(config.LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 設置日誌處理器
    handler = RotatingFileHandler(
        config.LOG_FILE,
        maxBytes=config.LOG_MAX_SIZE,
        backupCount=config.LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    
    # 設置日誌格式
    formatter = logging.Formatter(config.LOG_FORMAT)
    handler.setFormatter(formatter)
    
    # 設置根日誌記錄器
    root_logger = logging.getLogger()
    root_logger.setLevel(config.LOG_LEVEL)
    root_logger.addHandler(handler)
    
    # 同時輸出到控制台
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

def check_dependencies():
    """檢查必要的依賴和設定"""
    # 檢查 credentials.json
    if not os.path.exists(config.GOOGLE_APPLICATION_CREDENTIALS):
        raise FileNotFoundError(
            f"找不到 Google Cloud 憑證檔案：{config.GOOGLE_APPLICATION_CREDENTIALS}\n"
            "請確保已下載憑證檔案並放置在正確位置。"
        )
    
    # 檢查 Poppler（Windows）
    if os.name == 'nt':
        poppler_path = os.path.join(os.environ.get('PROGRAMFILES', 'C:\\Program Files'),
                                  'poppler', 'Library', 'bin')
        if not os.path.exists(poppler_path):
            raise EnvironmentError(
                "找不到 Poppler。請按照以下步驟安裝：\n"
                "1. 下載 Poppler for Windows\n"
                "2. 解壓縮到 C:\\Program Files\\poppler\n"
                "3. 將 C:\\Program Files\\poppler\\Library\\bin 加入系統環境變數 PATH"
            )

def main():
    """主程序"""
    try:
        # 設置日誌
        setup_logging()
        logging.info("開始執行 Gmail 附件處理程序")
        
        # 檢查依賴
        check_dependencies()
        logging.info("依賴檢查完成")
        
        # 建立處理器實例
        processor = GmailAttachmentProcessor()
        
        # 執行處理
        processor.process_emails()
        
        logging.info("處理完成")
        
    except Exception as e:
        logging.error(f"程序執行時發生錯誤：{str(e)}")
        logging.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main() 