from ..Utility import GeometricCalculation as GeomCalc
from ..SingleCellData import CellRect,CellIndex

import numpy as np

def getindexedCells(cellrects: list[CellRect]) -> list[CellIndex]:
    cellsdata = []
    for cellrect in cellrects:
        cellsdata.append({
            "Rect": cellrect,
            "Center": cellrect.center(),
            "SideLength": cellrect.meanSideLength()
        })
    _indexCells(cellsdata)
    return [cell["Index"] for cell in cellsdata]

def _indexCells(cellsdata: list[dict]):
    clusterindex = 0
    firstcellindex = _firstNonAsignedCellIndex(cellsdata)
    while firstcellindex != None:
        cellsdata[firstcellindex]["Index"] = CellIndex(clusterindex,0,0)
        _asignNextCellIndexes(firstcellindex, cellsdata)

        maxrow = max([cell["Index"].row for cell in cellsdata if "Index" in cell and cell["Index"].cluster == clusterindex])
        mincolumn = min([cell["Index"].column for cell in cellsdata if "Index" in cell and cell["Index"].cluster == clusterindex])
        for cell in cellsdata:
            if "Index" in cell and cell["Index"].cluster == clusterindex:
                cell["Index"].row = maxrow - cell["Index"].row
                cell["Index"].column -= mincolumn

        firstcellindex = _firstNonAsignedCellIndex(cellsdata)
        clusterindex += 1

def _firstNonAsignedCellIndex(cellsdata: list[dict]) -> int | None:
    for i, celldata in enumerate(cellsdata):
        if not "Index" in celldata:
            return i
    return None

def _asignNextCellIndexes(index, cellsdata: list[dict]):
    near = _getNearCellIndexes(index, cellsdata)
    for cellindex in near:
        angle = np.degrees(np.arctan2(cellsdata[cellindex]["Center"][1]-cellsdata[index]["Center"][1],
                                        cellsdata[cellindex]["Center"][0]-cellsdata[index]["Center"][0]))
        newindex = []
        if angle >= -45 and angle < 45:
            newindex = (cellsdata[index]["Index"].row,cellsdata[index]["Index"].column+1)
        elif angle >= 45 and angle < 135:
            newindex = (cellsdata[index]["Index"].row-1,cellsdata[index]["Index"].column)
        elif angle >= 135 or angle < -135:
            newindex = (cellsdata[index]["Index"].row,cellsdata[index]["Index"].column-1)
        elif angle >= -135 and angle < -45:
            newindex = (cellsdata[index]["Index"].row+1,cellsdata[index]["Index"].column)

        if not "Index" in cellsdata[cellindex]:
            cellsdata[cellindex]["Index"] = CellIndex(cellsdata[index]["Index"].cluster,newindex[0],newindex[1])
            _asignNextCellIndexes(cellindex, cellsdata)

def _getNearCellIndexes(index, cellsdata: list[dict]) -> list[int]:
    near: list[int] = []
    factor = 0.15
    for i,celldata in enumerate(cellsdata):
        if celldata["Center"] != cellsdata[index]["Center"] :
            dist = GeomCalc.distBetweenPoints(celldata["Center"],cellsdata[index]["Center"])
            if dist <= cellsdata[index]["SideLength"] * (1+factor) and dist >= cellsdata[index]["SideLength"] * (1-factor):
                near.append(i)
    return near
