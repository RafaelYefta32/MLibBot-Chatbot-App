import re

# ISBN 10/13 
ISBN_PATTERN = re.compile(
    r"\b(?:97[89][0-9\-]{10,16}|[0-9]{9}[0-9Xx])\b"
)

# Call number
CALLNUMBER_PATTERN = re.compile(
    r"\b\d{3}(?:\.\d+)?\s+[A-Z]{3}\s+[A-Z]\b"
)

YEAR_PATTERN = re.compile(r"\b(19|20)\d{2}\b")

def extract_isbn(text: str):
    return ISBN_PATTERN.findall(text)

def extract_callnumber(text: str):
    return CALLNUMBER_PATTERN.findall(text)

def extract_years(text: str):
    return YEAR_PATTERN.findall(text)
