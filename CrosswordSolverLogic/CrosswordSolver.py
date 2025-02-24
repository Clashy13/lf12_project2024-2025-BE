from .DataExtraction import CrossWordDataExtraction
from .DataInsertion import AnswerInput

def solve(imagepath):
    try:
        scannedimg, crossworddata = CrossWordDataExtraction.extractData(imagepath)
        return True
    except Exception as e:
        return e