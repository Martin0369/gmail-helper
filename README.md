# Gmail Helper

An automated system that processes Gmail attachments, particularly invoices and other business documents, and organizes them in Google Drive with intelligent categorization.

## Features

- Automatic Gmail attachment processing
- Smart document type identification (invoices, quotations, contracts, etc.)
- OCR-powered content extraction
- Intelligent file organization based on date, sender, and document type
- Multi-format invoice information extraction
- Automated folder structure creation
- Support for multiple languages (English, Traditional Chinese)

## System Requirements

- Python 3.8 or higher
- Windows, macOS, or Linux operating system
- Internet connection
- Google account

### Windows-specific Requirements

Windows users need to install Poppler for PDF processing:
1. Download [Poppler for Windows](https://github.com/oschwartz10612/poppler-windows/releases/)
2. Extract to `C:\Program Files\poppler`
3. Add `C:\Program Files\poppler\Library\bin` to system PATH

### macOS-specific Requirements

Install Poppler using Homebrew:
```bash
brew install poppler
```

### Linux-specific Requirements

Install Poppler using package manager:
```bash
# Ubuntu/Debian
sudo apt-get install poppler-utils

# CentOS/RHEL
sudo yum install poppler-utils
```

## Installation

1. Clone or download this repository:
   ```bash
   git clone https://github.com/Martin0369/gmail-helper.git
   cd gmail-helper
   ```

2. Create and activate virtual environment:
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Download Chinese language model:
   ```bash
   python -m spacy download zh_core_web_sm
   ```

## Configuration

1. Create Google Cloud Project and enable required APIs:
   - Gmail API
   - Google Drive API
   - Cloud Vision API

2. Download Google Cloud credentials:
   - Create a service account and download the key file (JSON format)
   - Rename the key file to `credentials.json` and place it in the project root

3. Set up configuration:
   - Copy `config.example.py` to `config.py`
   - Modify settings as needed

## Usage

1. Ensure all setup steps are completed

2. Run the program:
   ```bash
   python main.py
   ```

3. The program will automatically:
   - Check for new emails in Gmail
   - Download and process attachments
   - Organize and upload documents to Google Drive

## Folder Structure

The program creates the following structure in Google Drive:
```
YYYY_MM/
  ├── Sender/
  │   ├── Email Subject/
  │   │   ├── invoice_YYYYMMDD_Vendor_InvoiceNumber.pdf
  │   │   └── ...
  │   └── ...
  └── ...
```

## Troubleshooting

1. PDF Conversion Issues
   - Verify Poppler installation
   - Check system PATH settings

2. OCR Recognition Issues
   - Ensure Google Cloud Vision API is enabled
   - Verify credentials file configuration

3. Permission Issues
   - Confirm service account has necessary permissions
   - Check Gmail API and Drive API authorization scopes

## Document Processing

The system can process various types of documents:
- Invoices (Traditional Chinese and English)
- Quotations
- Contracts
- Purchase Orders
- Receipts

### Invoice Processing Features
- Extracts invoice numbers
- Identifies vendor information
- Captures invoice dates
- Processes amount information
- Handles multiple invoice formats

## Security

- All sensitive information is stored locally
- Credentials are never committed to version control
- Uses secure API authentication
- Implements file access controls

## Best Practices

- Regularly check log files for system status
- Back up important documents periodically
- Monitor Google Cloud project quotas
- Keep dependencies updated

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Google Cloud Platform for API services
- Spacy for NLP processing
- PyMuPDF and pdf2image for document processing
- All contributors and users of this project 