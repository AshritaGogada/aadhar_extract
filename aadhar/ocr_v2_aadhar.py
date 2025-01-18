from PIL import Image
import pytesseract
import argparse
import cv2
import os
import re
import io
import json
import ftfy

# Function to find the word matching a regular expression in a list of text
def findword(text_lines, pattern):
    for line in text_lines:
        match = re.search(pattern, line, re.IGNORECASE)  # Added IGNORECASE to match case-insensitively
        if match:
            return match.group(0)  # Return the first match found
    return None  # Return None if no match found

# Function to validate and format Date of Birth
def format_dob(dob):
    # Check if it's in the correct dd/mm/yyyy or yyyy format
    if re.match(r"^\d{2}/\d{2}/\d{4}$", dob):  # dd/mm/yyyy
        return dob
    elif re.match(r"^\d{4}$", dob):  # yyyy
        return dob
    else:
        return None  # Return None if the format is incorrect

# Section 1: Command line argument parsing
ap = argparse.ArgumentParser()
ap.add_argument("-i", "--image", required=True, help="path to input image to be OCR'd")
ap.add_argument("-p", "--preprocess", type=str, default="thresh", help="type of preprocessing (blur, linear, cubic, bilateral)")
args = vars(ap.parse_args())

# Section 2: Load and preprocess image
image = cv2.imread(args["image"])
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Preprocessing based on argument
if args["preprocess"] == "thresh":
    gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
elif args["preprocess"] == "adaptive":
    gray = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2)
elif args["preprocess"] == "linear":
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR)
elif args["preprocess"] == "cubic":
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
elif args["preprocess"] == "blur":
    gray = cv2.medianBlur(gray, 3)
elif args["preprocess"] == "bilateral":
    gray = cv2.bilateralFilter(gray, 9, 75, 75)
elif args["preprocess"] == "gauss":
    gray = cv2.GaussianBlur(gray, (5, 5), 0)

# Save temporary image for OCR processing
filename = "{}.png".format(os.getpid())
cv2.imwrite(filename, gray)

# Section 3: Run OCR using Tesseract
text = pytesseract.image_to_string(Image.open(filename), lang='eng')
os.remove(filename)

# Clean text using ftfy
text = ftfy.fix_text(text)
text = ftfy.fix_encoding(text)

# Write the OCR result to a text file
with open('outputbase.txt', 'w', encoding='utf-8') as text_output:
    text_output.write(text)

# Section 4: Extract relevant information
# Initialize variables
yob = None
gender = None
adhar = None
text1 = [line.strip() for line in text.split('\n') if line.strip()]

# Capture Year of Birth (ensure it's in correct format)
yob = findword(text1, r"\d{4}|\d{2}/\d{2}/\d{4}")  # Pattern for 4-digit year or dd/mm/yyyy format
if yob:
    yob = format_dob(yob)  # Check if DOB is in the correct format
else:
    yob = None  # Set to None if it's not in expected format

# Extract Gender (check for the presence of Male or Female)
gender = findword(text1, r"\b(Male|Female)\b")
if gender:
    gender = gender.strip()  # Ensure no leading or trailing spaces

# Extract Aadhar Number (match the format XXXX XXXX XXXX)
adhar = findword(text1, r"\d{4}\s\d{4}\s\d{4}")
if not adhar or not re.match(r"\d{4} \d{4} \d{4}", adhar):
    adhar = None  # Set to None if Aadhar is not in the correct format

# Store extracted data in a dictionary
data = {
    'Year of Birth': yob,
    'Gender': gender,
    'Aadhar': adhar
}

# Write the data to a JSON file
with io.open('data.json', 'w', encoding='utf-8') as outfile:
    json.dump(data, outfile, ensure_ascii=False, indent=4)

# Verify the content of the JSON file
with open('data.json', 'r', encoding='utf-8') as json_file:
    loaded_data = json.load(json_file)
    print(loaded_data)
