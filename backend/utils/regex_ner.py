import re

# ISBN 10/13 
isbn_pattern = re.compile(
    r"\b(?:97[89][0-9\-]{10,16}|[0-9]{9}[0-9Xx])\b"
)
def extract_isbn(text: str):
    return isbn_pattern.findall(text)

# Call number
callnumber_pattern = re.compile(
    r"\b\d{3}(?:\.\d+)?\s+[A-Z]{3}\s+[A-Z]\b"
)
def extract_callnumber(text: str):
    return callnumber_pattern.findall(text)

year_pattern = re.compile(r"\b(19|20)\d{2}\b")
def extract_years(text: str):
    return year_pattern.findall(text)