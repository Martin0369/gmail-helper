from setuptools import setup, find_packages

setup(
    name="gmail-helper",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "google-api-python-client>=2.108.0",
        "google-auth-httplib2>=0.1.1",
        "google-auth-oauthlib>=1.1.0",
        "google-cloud-vision>=3.4.4",
        "PyMuPDF>=1.23.7",
        "pdf2image>=1.16.3",
        "spacy>=3.7.2",
        "python-dotenv>=1.0.0"
    ],
    python_requires=">=3.8",
    author="Your Name",
    author_email="your.email@example.com",
    description="A Gmail attachment processor that automatically organizes documents in Google Drive",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    keywords="gmail, google-drive, document-processing, invoice-processing",
    url="https://github.com/yourusername/gmail-helper",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
) 