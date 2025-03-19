import PyPDF2
import pytesseract
from pytesseract import Output
import xlsxwriter
import re #import regex
import datetime
from dateutil.parser import *
import pandas
import datefinder
import ollama
from ollama import chat
from ollama import ChatResponse
import cv2


#Location of target PDF in directory
pdf_file_path = 'C:/Users/sfs/Downloads/DeepSeek Training Documents/'
pdf_file_name = 'SQF.pdf'

pdf_file_path += pdf_file_name

print(pdf_file_name)
print(pdf_file_path)

# Extracts text from PDF, non OCR
def extract_text_from_pdf(pdf_file_path):
    with open(pdf_file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ''
        for page_number in range (len(reader.pages)):
            page = reader.pages[page_number]
            text += page.extract_text()
        print(text)
        if (text == ''):
            image_text = pytesseract.image_to_string(pdf_file_path)
            print(image_text)    
        return text
    
#def ocr_pdf(pdf_file_path):
#Extracts incorrect, incoherent dates, triggered by any numbers in text
matches = datefinder.find_dates(extract_text_from_pdf(pdf_file_path))
for match in matches:
    print(match)
    
#response = ollama.chat("deepseek-r1:7b", "Hello, how can you assist me?")
#print(response)



#TODO use regex to filter and retain only relevant expiry dates
#Then pass through datefinder and strftime to format for Excel  
#def extract_expiry_dates_from_text(text):
    
