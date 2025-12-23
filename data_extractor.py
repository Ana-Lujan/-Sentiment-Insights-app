import requests
from bs4 import BeautifulSoup
from typing import List
import re
import logging

logger = logging.getLogger(__name__)

class ExtractionError(Exception):
    """Custom exception for data extraction errors."""
    pass

def extract_text_from_url(url: str) -> List[str]:
    """
    Extract text content from a URL using web scraping with robust error handling.

    Args:
        url (str): The URL to scrape

    Returns:
        List[str]: List of text lines extracted from the URL

    Raises:
        ExtractionError: If URL cannot be accessed or parsed
    """
    try:
        # Set headers to mimic a browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        # Make request with timeout
        response = requests.get(url.strip(), headers=headers, timeout=10)

        # Handle specific HTTP status codes
        if response.status_code == 401:
            raise ExtractionError("Acceso Denegado: La URL requiere inicio de sesión (Login) o es un API con restricciones de cuota/acceso. Use una fuente pública.")
        elif response.status_code == 403:
            raise ExtractionError("Acceso Denegado: La URL requiere inicio de sesión (Login) o es un API con restricciones de cuota/acceso. Use una fuente pública.")
        elif response.status_code == 404:
            raise ExtractionError("URL no válida o página no encontrada.")
        elif response.status_code == 429:
            raise ExtractionError("Demasiadas solicitudes. El sitio ha bloqueado temporalmente el acceso.")
        elif response.status_code >= 500:
            raise ExtractionError(f"Error del servidor ({response.status_code}). El sitio web tiene problemas técnicos.")
        elif response.status_code >= 400:
            raise ExtractionError(f"Error HTTP {response.status_code}: No se puede acceder a la URL.")

        # Only raise for status if it's not already handled above
        response.raise_for_status()

        # Parse HTML with explicit UTF-8 decoding
        soup = BeautifulSoup(response.content.decode('utf-8', errors='replace'), 'html.parser')

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Extract text from common content areas
        text_content = []

        # Try to get main content areas
        content_selectors = [
            'main', 'article', '.content', '.post', '.entry',
            '#content', '#main', '.article-body', '.post-content'
        ]

        main_content = None
        for selector in content_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break

        if main_content:
            text = main_content.get_text()
        else:
            # Fallback to body text
            text = soup.body.get_text() if soup.body else soup.get_text()

        # Apply content limit (first 5000 characters) to prevent processing huge websites
        text = text[:5000]

        # Remove null bytes and other problematic characters that can cause encoding issues
        text = text.replace('\x00', '').replace('\ufeff', '')
        # Remove other potentially problematic Unicode characters
        text = ''.join(char for char in text if ord(char) < 65536)  # Keep only BMP characters

        # Clean and split text
        lines = []
        for line in text.split('\n'):
            line = line.strip()
            # Skip very short lines and lines that are mostly punctuation
            if len(line) > 10 and not re.match(r'^[^\w\s]*$', line):
                lines.append(line)

        if not lines:
            raise ExtractionError("No se encontró contenido de texto legible en la página.")

        logger.info(f"Successfully extracted {len(lines)} text lines from URL: {url}")
        return lines

    except requests.exceptions.Timeout:
        raise ExtractionError("Tiempo de espera agotado al acceder a la URL.")
    except requests.exceptions.RequestException as e:
        raise ExtractionError(f"Fallo al acceder a la URL: {str(e)}")
    except ExtractionError:
        # Re-raise our custom exceptions
        raise
    except Exception as e:
        raise ExtractionError(f"Error procesando el contenido de la URL: {str(e)}")

def extract_text_from_file(file_content: bytes, filename: str) -> List[str]:
    """
    Extract text lines from uploaded file content.

    Args:
        file_content (bytes): The file content as bytes
        filename (str): The original filename

    Returns:
        List[str]: List of text lines from the file

    Raises:
        ValueError: If file cannot be processed
    """
    try:
        # Decode text content
        text = file_content.decode('utf-8', errors='ignore')

        # Split into lines and clean
        lines = []
        for line in text.split('\n'):
            line = line.strip()
            if line and len(line) > 2:  # Skip very short lines
                lines.append(line)

        if not lines:
            raise ValueError("No readable text content found in file")

        logger.info(f"Successfully extracted {len(lines)} text lines from file: {filename}")
        return lines

    except UnicodeDecodeError:
        raise ValueError("File encoding not supported. Please use UTF-8 encoded text files.")
    except Exception as e:
        raise ValueError(f"Error processing file content: {str(e)}")

def validate_url(url: str) -> bool:
    """
    Basic URL validation.

    Args:
        url (str): URL to validate

    Returns:
        bool: True if URL is valid
    """
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    return url_pattern.match(url.strip()) is not None