"""Main"""
import os
#from .database_handler import get_db_connection
#from .csv_handler import *
from configg import PathConfig
from .pdf_extract import pdf_to_text, text_to_json
from .database_handler import insert_into_db

def main():
    """Main"""
    #print sys.path
    input_file = PathConfig.INPUT_DIR
    output_file = PathConfig.OUTPUT_DIR

    # Extract text from PDF
    #pdf_to_text(input_file, output_file)
    print("The text has been extracted")

    # Extract JSON object literal list from text
    json_list = text_to_json(output_file)

    # Create db out of list of documents
    insert_into_db(json_list)

    print("The program is over")
    print(os.getcwd())

if __name__ == "__main__":
    main()

# End of file
