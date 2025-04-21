class CellIndex:
    def __init__(self, cluster: int, row: int, column: int):
        self.cluster = cluster
        self.row = row
        self.column = column

    def __eq__(self, other):
        if (other.cluster == self.cluster and
            other.row == self.row and
            other.column == self.column):
            return True
        return False
