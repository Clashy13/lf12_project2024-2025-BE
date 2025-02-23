from .QuestionLine import QuestionLine
from ..SingleCellData import CellRect

class ClusterData:
    def __init__(self, questionlines: list[QuestionLine], answerrects: list[CellRect]):
        self.questionlines = questionlines
        self.answerrects = answerrects
