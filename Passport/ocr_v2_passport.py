# import the necessary packages
from PIL import Image
import pytesseract
import argparse
import cv2
import os
import re
import io
import json
import ftfy

################################################################################################################
############################# Section 1: Initiate the command line interface ###################################
################################################################################################################

# construct the argument parse and parse the arguments
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

# load the example image and convert it to grayscale
image = cv2.imread(args["image"])
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# check to see if we should apply thresholding to preprocess the
# image
if args["preprocess"] == "thresh":
    gray = cv2.threshold(gray, 0, 255,
                         cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

elif args["preprocess"] == "adaptive":
    gray = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2)

if args["preprocess"] == "linear":
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR)

elif args["preprocess"] == "cubic":
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

# make a check to see if blurring should be done to remove noise, first is default median blurring
if args["preprocess"] == "blur":
    gray = cv2.medianBlur(gray, 3)

elif args["preprocess"] == "bilateral":
    gray = cv2.bilateralFilter(gray, 9, 75, 75)

elif args["preprocess"] == "gauss":
    gray = cv2.GaussianBlur(gray, (5,5), 0)

# write the grayscale image to disk as a temporary file so we can
# apply OCR to it
filename = "{}.png".format(os.getpid())
cv2.imwrite(filename, gray)

##############################################################################################################
######################################## Section 3: Running PyTesseract ######################################
##############################################################################################################


# load the image as a PIL/Pillow image, apply OCR, and then delete
# the temporary file
text = pytesseract.image_to_string(Image.open(filename), lang = 'eng')
os.remove(filename)

# writing extracted data into a text file
text_output = open('outputbase.txt', 'w', encoding='utf-8')
text_output.write(text)
text_output.close()

file = open('outputbase.txt', 'r', encoding='utf-8')
text = file.read()

# Cleaning all the gibberish text
text = ftfy.fix_text(text)
text = ftfy.fix_encoding(text)

############################################################################################################
###################################### Section 4: Extract relevant information #############################
############################################################################################################

# Initializing data variable
surname = None
first_name = None
dob = None
gender = None
number = None
doe = None
text0 = []
text1 = []

# Searching for PAN
lines = text.split('\n')
for lin in lines:
    s = lin.strip()
    s = lin.replace('\n','')
    s = s.rstrip()
    s = s.lstrip()
    text1.append(s)

text1 = list(filter(None, text1))

# to remove any text read from the image file which lies before the line 'Income Tax Department'
lineno = 0  # to start from the first line of the text file.
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
    surname_line = [line for line in text0 if re.search(r'^[A-Z]+$', line)]
    surname = surname_line[0] if surname_line else ""
    surname = re.sub('[^a-zA-Z]+', ' ', surname)

    # Extracting First Name
    first_name_line = [line for line in text0 if re.search(r'[A-Z]{2,}', line)]
    first_name = first_name_line[1] if first_name_line else ""
    first_name = re.sub('[^a-zA-Z]+', ' ', first_name)

    # Extracting Date of Birth (DOB) and ensuring it's in dd/mm/yyyy format
    dob_line = [line for line in text0 if re.search(r'\d{2}/\d{2}/\d{4}', line)]
    dob = dob_line[0] if dob_line else ""
    
    # Extracting Gender (M/F)
    gender_line = [line for line in text0 if re.search(r'[M|F]', line)]
    gender = gender_line[0] if gender_line else "M"  # Assuming 'M' for male if not found
    
    # Extracting Passport Number
    passport_line = [line for line in text0 if re.search(r'\b[A-Z]{2}\d{7}\b', line)]
    number = passport_line[0] if passport_line else ""
    
    # Extracting Date of Expiry (DOE)
    doe_line = [line for line in text0 if re.search(r'\d{2}/\d{2}/\d{4}', line)]
    doe = doe_line[1] if doe_line and len(doe_line) > 1 else ""

except Exception as e:
    print(f"Error: {e}")

# Creating final data structure
data = {}
data['Surname'] = surname
data['First Name'] = first_name
data['Date of Birth'] = dob
data['Gender'] = gender
data['Number'] = number
data['Date of Expiry'] = doe

###############################################################################################################
######################################### Section 6: Write Data to JSON ######################################
###############################################################################################################

# Writing data into JSON
try:
    to_unicode = unicode
except NameError:
    to_unicode = str

# Write JSON file
with io.open('data.json', 'w', encoding='utf-8') as outfile:
    str_ = json.dumps(data, indent=4, sort_keys=True, separators=(',', ': '), ensure_ascii=False)
    outfile.write(to_unicode(str_))

# Read JSON file
with open('data.json', encoding = 'utf-8') as data_file:
    data_loaded = json.load(data_file)

# Reading data back from JSON
with open('data.json', 'r', encoding= 'utf-8') as f:
    ndata = json.load(f)

print(ndata)  # Printing the extracted and cleaned data

