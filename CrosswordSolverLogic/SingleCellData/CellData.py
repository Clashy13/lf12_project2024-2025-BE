from .CellRect import CellRect
from .CellIndex import CellIndex
from .CellContentData import CellContentData

class CellData:
    def __init__(self, rect: CellRect, index: CellIndex, content: CellContentData):
        self.rect = rect
        self.index = index
        self.content = content

    def __eq__(self, other):
        return self.index == other.index
