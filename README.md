# Gmail 附件處理助手

這個專案可以自動處理 Gmail 中的附件，特別是發票等文件，並將其整理存放到 Google Drive 中。

## 功能特點

- 自動處理 Gmail 中的附件
- 智能識別文件類型（發票、報價單、合約等）
- 使用 OCR 技術提取文件內容
- 根據日期、寄件者和文件類型自動整理檔案
- 支援多種發票格式的資訊提取
- 自動建立有組織的資料夾結構

## 系統需求

- Python 3.8 或更高版本
- Windows、macOS 或 Linux 作業系統
- 網際網路連線
- Google 帳號

### Windows 特殊需求

Windows 用戶需要安裝 Poppler，用於 PDF 處理：
1. 下載 [Poppler for Windows](https://github.com/oschwartz10612/poppler-windows/releases/)
2. 解壓縮到 `C:\Program Files\poppler`
3. 將 `C:\Program Files\poppler\Library\bin` 加入系統環境變數 PATH

### macOS 特殊需求

使用 Homebrew 安裝 Poppler：
```bash
brew install poppler
```

### Linux 特殊需求

安裝 Poppler：
```bash
# Ubuntu/Debian
sudo apt-get install poppler-utils

# CentOS/RHEL
sudo yum install poppler-utils
```

## 安裝步驟

1. 克隆或下載此專案：
   ```bash
   git clone [repository_url]
   cd gmail-helper
   ```

2. 建立並啟動虛擬環境：
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. 安裝依賴套件：
   ```bash
   pip install -r requirements.txt
   ```

4. 下載中文語言模型：
   ```bash
   python -m spacy download zh_core_web_sm
   ```

## 設定步驟

1. 建立 Google Cloud Project 並啟用必要的 API：
   - Gmail API
   - Google Drive API
   - Cloud Vision API

2. 下載 Google Cloud 憑證：
   - 建立服務帳號並下載金鑰檔案（JSON 格式）
   - 將金鑰檔案重新命名為 `credentials.json` 並放在專案根目錄

3. 建立設定檔：
   - 複製 `config.example.py` 為 `config.py`
   - 根據需求修改設定值

## 使用方法

1. 確保已完成所有設定步驟

2. 執行程式：
   ```bash
   python main.py
   ```

3. 程式會自動：
   - 檢查 Gmail 中的新郵件
   - 下載並處理附件
   - 將文件整理並上傳到 Google Drive

## 資料夾結構

程式會在 Google Drive 中建立以下結構：
```
YYYY_MM/
  ├── 寄件者/
  │   ├── 郵件主旨/
  │   │   ├── invoice_YYYYMMDD_賣方_發票號碼.pdf
  │   │   └── ...
  │   └── ...
  └── ...
```

## 故障排除

1. PDF 轉換失敗
   - 確認 Poppler 已正確安裝
   - 檢查系統環境變數設定

2. OCR 辨識失敗
   - 確認 Google Cloud Vision API 已啟用
   - 檢查憑證檔案設定

3. 權限問題
   - 確認服務帳號擁有必要的權限
   - 檢查 Gmail API 和 Drive API 的授權範圍

## 注意事項

- 請確保 Google Cloud 專案有足夠的配額
- 定期檢查日誌檔案了解系統運行狀況
- 建議定期備份重要文件

## 授權

[授權說明]

## 貢獻

歡迎提交 Issue 或 Pull Request 來改善這個專案。 