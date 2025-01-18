# Import necessary packages
from PIL import Image
import pytesseract
import argparse
import cv2
import os
import re
import io
import json
import ftfy
# from utils.utils import classify_document
import sys
import os
################################################################################################################
############################# Section 1: Initiate the command line interface ###################################
################################################################################################################

# parent_dir = os.path.dirname(os.getcwd())
# utils_path = os.path.join(parent_dir, '../utils')
# sys.path.append(utils_paths)
# Construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-i", "--image", required=True,
                help="path to input image to be OCR'd")
ap.add_argument("-p", "--preprocess", type=str, default="thresh",
                help="type of preprocessing to be done, choose from blur, linear, cubic or bilateral")
args = vars(ap.parse_args())

'''
Our command line arguments are parsed. We have two command line arguments:

--image : The path to the image we’re sending through the OCR system.
--preprocess : The preprocessing method. This switch is optional and for this tutorial and can accept the following 
                parameters to be passed (refer sections to know more:
                - blur
                - adaptive
                - linear
                - cubic
                - gauss
                - bilateral
                - thresh (meadian threshold - default)
---------------------------  Use Blur when the image has noise/grain/incident light etc. --------------------------
'''

##############################################################################################################
###################### Section 2: Load the image -- Preprocess it -- Write it to disk ########################
##############################################################################################################

# Load the example image and convert it to grayscale
image = cv2.imread(args["image"])
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Check to see if we should apply thresholding to preprocess the image
if args["preprocess"] == "thresh":
    gray = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)[1]

elif args["preprocess"] == "adaptive":
    gray = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 2)

elif args["preprocess"] == "linear":
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR)

elif args["preprocess"] == "cubic":
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

elif args["preprocess"] == "blur":
    gray = cv2.medianBlur(gray, 3)

elif args["preprocess"] == "bilateral":
    gray = cv2.bilateralFilter(gray, 9, 75, 75)

elif args["preprocess"] == "gauss":
    gray = cv2.GaussianBlur(gray, (5,5), 0)

# Write the grayscale image to disk as a temporary file so we can apply OCR to it
filename = "{}.png".format(os.getpid())
cv2.imwrite(filename, gray)

##############################################################################################################
######################################## Section 3: Running PyTesseract ######################################
##############################################################################################################

# Load the image as a PIL/Pillow image, apply OCR, and then delete the temporary file
text = pytesseract.image_to_string(Image.open(filename), lang='eng')
os.remove(filename)

# Write extracted data into a text file
text_output = open('outputbase.txt', 'w', encoding='utf-8')
text_output.write(text)
text_output.close()

# Read text from file
file = open('outputbase.txt', 'r', encoding='utf-8')
text = file.read()

# Clean the text
text = ftfy.fix_text(text)
text = ftfy.fix_encoding(text)

############################################################################################################
###################################### Section 4: Extract relevant information #############################
############################################################################################################

# Initialize variables
surname = None
first_name = None
dob = None
gender = None
number = None
doe = None
text0 = []
text1 = []

# Search for PAN
lines = text.split('\n')
for lin in lines:
    s = lin.strip()
    s = lin.replace('\n','')
    s = s.rstrip()
    s = s.lstrip()
    text1.append(s)

text1 = list(filter(None, text1))

# To remove any text read from the image file which lies before the line 'Income Tax Department'
lineno = 0  # To start from the first line of the text file.
text0 = text1[lineno+1:]

def findword(textlist, wordstring):
    lineno = -1
    for wordline in textlist:
        xx = wordline.split()
        if ([w for w in xx if re.search(wordstring, w)]):
            lineno = textlist.index(wordline)
            textlist = textlist[lineno+1:]
            return textlist
    return textlist

###############################################################################################################
######################################### Section 5: Extracting Data ##########################################
###############################################################################################################
try:
    # Extracting Surname
    surname = text0[3].strip()
    surname = re.sub('[^a-zA-Z]+', ' ', surname)

    # Extracting First Name
    first_name = text0[5].strip()
    first_name = re.sub('[^a-zA-Z]+', ' ', first_name)

    # Extracting Date of Birth - More robust regex
    dob = text0[7].strip()
    dob = re.sub('[^0-9/]+', '', dob)

    # Extracting Gender
    gender = 'M'  # Assuming gender is always 'M' for this case

    # Extracting Passport Number
    number = text0[1].strip()[-8:]  # Assuming passport number is at the start of the line

    # Extracting Date of Expiry
    doe = text0[14].strip()
    doe = re.sub('[^0-9/]+', '', doe)

except Exception as e:
    print(f"Error during extraction: {e}")

# Making tuples of extracted data
data = {
    'Surname': surname,
    'First Name': first_name,
    'Date of Birth': dob,
    'Gender': gender,
    'Number': number,
    'Date of Expiry': doe
}

###############################################################################################################
######################################### Section 6: Write Data to JSON ######################################
###############################################################################################################

# Write the extracted data into JSON
with io.open('data.json', 'w', encoding='utf-8') as outfile:
    json.dump(data, outfile, ensure_ascii=False, indent=4)

# Read and display the cleaned data from JSON
with open('data.json', encoding='utf-8') as f:
    ndata = json.load(f)

print(ndata)  # Verify the cleaned and corrected data
def classify_document(text):

    if re.search(r"\d{4} \d{4} \d{4}", text):
        return "Aadhaar"
    elif re.search(r"[A-Z]{5}\d{4}[A-Z]", text):
        return "PAN"
    elif re.search(r"[A-Z]\d{7}", text):
        return "Passport"
    else:
        return "Unknown"

document_type = classify_document(text)
print(f"Document type: {document_type}")
