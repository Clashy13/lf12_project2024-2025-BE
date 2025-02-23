from .CellRect import CellRect

class SolutionCellData:
    def setRect(self, rect: CellRect):
        self.rect = rect

    def setClusterIndexReference(self, clusterindexref: int):
        self.clusterindexref = clusterindexref

    def setClusterCellIndexReference(self, clustercellindexref: int):
        self.clustercellindexref = clustercellindexref
