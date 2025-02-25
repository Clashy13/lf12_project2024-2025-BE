from ..SingleCellData import SolutionCellData
from .ClusterData import ClusterData

class CrossWordData:
    def __init__(self, clustersdata: list[ClusterData], solutioncells: list[SolutionCellData]):
        self.clustersdata = clustersdata
        self.solutioncells = solutioncells
        
    def toDict(self) -> dict:
        datadict = {}
        datadict["Solution"] = []
        for cell in self.solutioncells:
            datadict["Solution"].append({
                "Rect": [(int(p[0]),int(p[1])) for p in cell.rect],
                "ClusterIndex": cell.clusterindexref,
                "CellIndex": cell.clustercellindexref
            })

        datadict["Cluster"] = []
        for cluster in self.clustersdata:
            clusterdata = {}
            clusterdata["Questions"] = []
            for questionline in cluster.questionlines:
                clusterdata["Questions"].append({
                    "Question":questionline.question,
                    "CellIndexes": questionline.cellindexes
                })
            clusterdata["CellRects"] = []
            for rect in cluster.answerrects:
                clusterdata["CellRects"].append([(int(p[0]),int(p[1])) for p in rect])
            datadict["Cluster"].append(clusterdata)
        return datadict
