from .CellDataType import ArrowsData,NumberData
from .SingleQuestionData import SingleQuestionData
from .DoubleQuestionData import DoubleQuestionData

class CellContentData:
    number: NumberData = 0
    arrows: ArrowsData = []
    doublequestion: DoubleQuestionData | None = None
    singlequestion: SingleQuestionData | None = None
    blank = False