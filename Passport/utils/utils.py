import re
def classify_document(text):

    if re.search(r"\d{4} \d{4} \d{4}", text):
        return "Aadhaar"
    elif re.search(r"[A-Z]{5}\d{4}[A-Z]", text):
        return "PAN"
    elif re.search(r"[A-Z]\d{7}", text):
        return "Passport"
    else:
        return "Unknown"

# Example usage
