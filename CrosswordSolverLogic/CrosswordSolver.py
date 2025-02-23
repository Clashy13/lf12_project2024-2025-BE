from .DataExtraction import CrossWordDataExtraction
from .DataInsertion import AnswerInput

def solve(imagepath):
    try:
        scannedimg, crossworddata = CrossWordDataExtraction.extractData(imagepath)
    except Exception as e:
        print(e)