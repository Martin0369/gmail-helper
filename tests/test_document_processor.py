import pytest
from document_processor import DocumentProcessor
import os
import json

@pytest.fixture
def document_processor():
    return DocumentProcessor()

@pytest.fixture
def sample_invoice_text():
    return """
    統一發票
    發票號碼：AB-12345678
    日期：2024年03月15日
    統一編號：12345678
    
    買受人：測試公司
    賣方：範例企業有限公司
    
    品項：
    1. 商品A $1,000
    2. 商品B $2,000
    
    總計：NT$3,000
    """

def test_classify_document(document_processor, sample_invoice_text):
    doc_type = document_processor._classify_document(sample_invoice_text)
    assert doc_type == 'invoice'

def test_extract_invoice_info(document_processor, sample_invoice_text):
    doc = document_processor.nlp(sample_invoice_text)
    info = document_processor._extract_invoice_info(sample_invoice_text, doc)
    
    assert info['invoice_number'] == 'AB12345678'
    assert info['invoice_date'] == '2024-03-15'
    assert info['tax_id'] == '12345678'
    assert '範例企業' in info['seller']
    assert info['amount'] == '3000'

def test_pdf_to_images(document_processor, tmp_path):
    # Create a simple PDF file for testing
    pdf_path = tmp_path / "test.pdf"
    with open(pdf_path, 'wb') as f:
        f.write(b'%PDF-1.4\n%EOF')
    
    with open(pdf_path, 'rb') as f:
        pdf_data = f.read()
    
    images = document_processor._pdf_to_images(pdf_data)
    assert isinstance(images, list)

def test_perform_ocr(document_processor):
    # Mock image data for testing
    image_data = b'fake_image_data'
    
    # This should return empty string for fake data
    result = document_processor._perform_ocr(image_data)
    assert isinstance(result, str) 