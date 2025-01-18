# Import the necessary packages
from PIL import Image
import pytesseract
import argparse
import cv2
import os
import re
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

##############################################################################################################
###################### Section 2: Load the image -- Preprocess it -- Write it to disk ########################
##############################################################################################################

# load the example image and convert it to grayscale
image = cv2.imread(args["image"])
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# check to see if we should apply thresholding to preprocess the image
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

# write the grayscale image to disk as a temporary file
filename = "{}.png".format(os.getpid())
cv2.imwrite(filename, gray)

##############################################################################################################
######################################## Section 3: Running PyTesseract ######################################
##############################################################################################################

# load the image as a PIL/Pillow image, apply OCR, and then delete the temporary file
text = pytesseract.image_to_string(Image.open(filename), lang='eng')
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
name = None
fname = None
dob = None
pan = None
text1 = []

# Splitting lines
lines = text.split('\n')
for lin in lines:
    s = lin.strip()
    s = lin.replace('\n', '')
    s = s.rstrip()
    s = s.lstrip()
    text1.append(s)
text1 = list(filter(None, text1))

# Debugging: Check the first few lines of text
print("First few lines of OCR text:", text1[:5])

# to remove any text read from the image file which lies before the line 'Income Tax Department'
lineno = 0
for wordline in text1:
    if re.search(r'(INCOMETAXDEPARTMENT|INCOME|TAX|GOVERNMENT|DEPARTMENT|INDIA)', wordline):
        lineno = text1.index(wordline)
        break
text0 = text1[lineno + 1:]

# Function to find and return data after a specific keyword
def find_after_keyword(textlist, keyword):
    for wordline in textlist:
        if keyword.lower() in wordline.lower():
            index = textlist.index(wordline) + 1
            return textlist[index] if index < len(textlist) else None
    return None

###############################################################################################################
######################################### Section 5: Extracting Information ###################################
###############################################################################################################

try:
    # Extract Name
    name = find_after_keyword(text1, 'Name')
    if name:
        name = name.strip()
    else:
        name = "Not found"
    print(f"Extracted Name: {name}")

    # Extract Father's Name
    fname = find_after_keyword(text1, "Father's Name")
    if fname:
        fname = fname.strip()
    else:
        fname = "Not found"
    print(f"Extracted Father's Name: {fname}")

    # Extract Date of Birth
    dob = find_after_keyword(text1, 'Date of Birth')
    if dob:
        dob = dob.strip()
    dob = re.sub('[^0-9/]', '', dob)  # Ensuring only valid date characters
    print(f"Extracted Date of Birth: {dob}")

    # Extract PAN Number
    pan = find_after_keyword(text1, 'Permanent Account Number')
    if pan:
        pan = pan.strip().replace(" ", "")
    else:
        pan = "Not found"
    print(f"Extracted PAN: {pan}")

except Exception as e:
    print(f"An error occurred: {e}")

# Prepare the data dictionary
data = {
    'Name': name,
    'Father Name': fname,
    'Date of Birth': dob,
    'PAN': pan
}

# Output the extracted data to a JSON file
with open('data.json', 'w', encoding='utf-8') as json_file:
    json.dump(data, json_file, indent=4)
