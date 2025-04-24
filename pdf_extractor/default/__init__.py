from PyPDF2 import PdfReader
import pytesseract
from pytesseract import Output
import xlsxwriter
import re 
from datetime import date
from dateutil.parser import *
import pandas
import datefinder
import ollama
from ollama import chat
from ollama import ChatResponse
import cv2
import os
import ocrmypdf
import subprocess
import json
import time
from pydantic import BaseModel
from test.support._hypothesis_stubs import strategies
from cv2.gapi import streaming
import string 
from typing import List
from pickle import FALSE


schema = '''{
    issue_date: string
    expiry_date: string
    document_type: string
    }'''

class Pdf(BaseModel):
    issue_date: date
    expiry_date: date
    document_type: str
    
class PdfList(BaseModel):
    pdfs: List[Pdf]
        

def extract_text_from_pdf(pdf_file_path):
    # Extracts both native and OCR text from PDF using PyPDF2 
    with open(pdf_file_path, 'rb') as file:
        reader = PdfReader(file)
        print(file)
        text = ''
        
        for page_number in range (len(reader.pages)):
            # I don't like long documents, first 2 pages only
            if page_number < 3:
                page = reader.pages[page_number]
                text += page.extract_text() or ""
       
        #print(text)   
        return text
    
def ocr_pdf(pdf_path, ocr_output_path):
    # OCRs a PDF using OCRmyPDF
    has_text = bool(extract_text_from_pdf(pdf_path))
    
    try:
        if not has_text:
            # No existing text
            ocrmypdf.ocr(
                pdf_path,
                ocr_output_path,
                force_ocr=True,  # Will OCR even if text exists
                skip_text=False,     # Don't skip pages with text
                optimize=1,          # Optimize the PDF after OCR
                progress_bar=False,   # Disable progress bar in programmatic use
                deskew=True,
                clean_final=True,
                remove_background=False,
                invalidate_digital_signatures=True
            )
        else: 
            process_pdf_safely(pdf_path, ocr_output_path)
        return True
    except Exception as e:
        print(f"OCR failed: {e}")
        return False
     
def process_pdf_safely(pdf_path, ocr_output_path):
    try:
        # First try with redo_ocr enabled (most efficient)
        ocrmypdf.ocr(
            pdf_path,
            ocr_output_path,
            force_ocr=False,
            redo_ocr=True,
            skip_text=False,
            optimize=1,
            progress_bar=False,
            # Disable incompatible features
            deskew=False,
            clean_final=False,
            remove_background=False,
            invalidate_digital_signatures=True
        )
        print("Successfully processed with redo_ocr")
    except ocrmypdf.exceptions.PriorOcrFoundError:
        print("Found existing OCR - falling back to force_ocr")
        # Fall back to force_ocr if redo_ocr fails
        ocrmypdf.ocr(
            pdf_path,
            ocr_output_path,
            force_ocr=True,
            skip_text=False,
            optimize=1,
            progress_bar=False,
            # Can use preprocessing features here
            deskew=True,
            clean_final=True,
            remove_background=False,  # Still often problematic :(
            invalidate_digital_signatures=True
        )
    
def pdf_to_text(input_dir, output_dir):
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    for filename in os.listdir(input_dir):
        if filename.endswith('.pdf'):
            pdf_path = os.path.join(input_dir, filename) # Input PDF
            ocr_output_path = os.path.join(input_dir, f"ocr_{filename}") # OCR'd output
            text_output_path = os.path.join(output_dir, f"{os.path.splitext(filename)[0]}.txt") # Final text output
            
            # STEP 1: Extract text using PyPDF2
            extracted_text = extract_text_from_pdf(pdf_path)
            
            # STEP 2: OCR all PDFs
            try:
                if not extracted_text.strip():
                    print("No text found - performing OCR")
                    ocr_success = ocr_pdf(pdf_path, ocr_output_path)
                else:
                    print("Text found - performing enhanced OCR")
                    ocr_success = ocr_pdf(pdf_path, ocr_output_path)
                
                # STEP 3: Get final text (from OCR'd version if successful)
                if ocr_success:
                    extracted_text = extract_text_from_pdf(ocr_output_path)
                
                # Write output file
                with open(text_output_path, 'w', encoding='utf-8') as text_file:
                    filetitle = filename.removesuffix(".pdf")
                    text_file.write(f"{filetitle}\n")
                    text_file.write(extracted_text)
                    
            except Exception as e:
                print(f"Something went wrong: {e}")  
                
            finally:
                # Clean up OCR temp file if it exists
                if os.path.exists(ocr_output_path):
                    os.remove(ocr_output_path)      
            
    
def text_to_json(text_input_dir):
    # Iterates over each file in the directory and queries local model about each one
    print("We are in the function text_to_json.\n")
    all_pdfs = []
    for filename in os.listdir(text_input_dir):
        if filename.endswith('.txt'):
            file_path = os.path.join(text_input_dir, filename)
            with open(file_path, 'r', encoding='utf-8') as file:
                file_content = file.read()
                
                filetitle = filename.removesuffix('.txt')
                print("We are about to query the local language model with the following prompt:\n")
                # Prompt for local model
                prompt = """
                    Key-Value Pair Instructions: 'issue_date' may be preceded by different titles, such as 'issue 
                    date', 'created', 'revised', 'signed','decision' or 'issued'.  If a text has only date in it, that is the issue 
                    date. All dates are between the years 2000 and 2050. Some text files may not have any dates at all. In this case, the 'issue_date' output value should 
                    be 'none'. 'expiry_date' may be preceded by different titles, such as 'valid', 'valid through', 'valid until', 
                    'until', 'expires', 'expiry date', 'expiry', 'exp' or 'expires on'. The expiry date should be a later date 
                    than the issue date. All dates are between the years 2000 and 2050. Some text files may not have an expiry date. If the text has an 'issue_date' but 
                    no 'expiry_date', the 'expiry_date' output value should be a date that is 3 years after 'issue_date'. 
                    If the text has neither an expiry date or an issue date, the 'expiry_date' value should be 'none'.
                    document_type must be of a type you would expect to receive from a food production supplier. 
                    Here are some examples: GFSI Certificate (FSSC 22000, BRCGS, IFS, SQF, BRC), GFSI Audit Report 
                    (FSSC 22000, BRCGS, IFS, SQF, BRC), Kosher Certificate, Kosher Statement, Halal Certificate, 
                    Halal Statement, HACCP Certificate, HACCP Flow Chart, GMP Policy, Food Defense Statement, 
                    Ethical Policy, Ethical Statement, Vegan Statement, Vegan Declaration, Organic Certificate, 
                    Organic Statement, Food Manufacturing License, TNPP Declaration, Product Assurance Statement, 
                    Product Specification, Letter of Guarantee, Continuing Guarantee, Allergen Statement, 
                    Allergen Policy, Heavy Metal Statement, Certificate of Liability Insurance, FDA Registration, 
                    Country of Origin, Recall Plan, Product Recall, Emergency Contacts, Letter of Compliance, 
                    Pesticide Statement, Ethical Policy, Ethical Statement, Non-GMO Statement, Food Defense Plan, 
                    Food Defense Statement, Food Fraud Statement, Food Fraud Plan, Bioterrorism Statement, 
                    TACCP, Code of Conduct, Lot Code Statement, Lot Code Explanation, etc. If the document is not of any recognizable type, the 'document_type' 
                    output value should be the title of the text file. Please fill in these key-value pairs \n
                    {\n\"issue_date\": , \n\"expiry_date\": , \n\"document_type\": \n} 
                    \nwith information from the following text, and output the answer in valid JSON object literal format:\n
                """
                prompt += f"{filetitle}\n{file_content}"
                
                
                response = chat(
                    model='qwen2.5:7b',
                    messages=[{'role': 'user', 'content': prompt}],
                    format=PdfList.model_json_schema(),
                    options={'temperature': 0},
                    )
                
                pdf_data = PdfList.model_validate_json(response.message.content)
                print(pdf_data)
                all_pdfs.extend(pdf_data.pdfs)
                
                
                # Delay to prevent overload of computer or local model
                print("\nWe will now wait for 10 seconds...")
                time.sleep(10)
                #temp = json.loads(result.message.content)
                
    pdf_dicts = [pdf.model_dump() for pdf in all_pdfs]  # Pydantic v2 (or .dict() for v1)
    df = pandas.DataFrame(pdf_dicts)
    
    # Export to Excel sheet
    df.to_excel("all_certificates.xlsx", index=False)
    
    
if __name__ == "__main__":
    input_dir = "C:/Users/sfs/Downloads/DeepSeek Training Documents/Test"
    output_dir = "C:/Users/sfs/Documents/DeepSeek_Text_Files"
    #print(input_dir)
    #print(output_dir)
    
    # Extract text from PDF
    pdf_to_text(input_dir, output_dir)
    print("The text has been extracted")
    
    # Extract JSON object literal from text
    #text_to_json(output_dir)
    print("The program is over")
    print(os.getcwd())
