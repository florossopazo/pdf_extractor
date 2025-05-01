"""Configurations"""
from pathlib import Path

DB_CONFIG = {
    """Module"""
    'host': 'localhost',
    'user' : 'SFS',
    'password' : 'Smart.Food!657',
    'database' : 'my_database'
}

class PathConfig:
    """Doc"""
    INPUT_DIR = "C:/Users/sfs/Downloads/pdf_extractor_input/Test"
    OUTPUT_DIR = "C:/Users/sfs/Documents/pdf_extractor_output"


    @classmethod
    def setup(cls, input_dir=None, output_dir=None):
        cls.INPUT = Path(input_dir) if input_dir else cls.INPUT
        cls.OUTPUT = Path(output_dir) if output_dir else cls.OUTPUT
        cls.INPUT.mkdir(exist_ok=True)
        cls.OUTPUT.mkdir(exist_ok=True)
# End of file