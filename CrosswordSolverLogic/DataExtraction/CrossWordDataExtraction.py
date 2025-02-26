from . import CrossWordScanning as Scan
from . import CellRectExtraction as CellRectExtr
from . import CollectiveCellsDataExtraction as CellsDataExtr
from ..SingleCellData import CellRect
from ..CollectiveCellData import CrossWordData
from ..Type import Cv2Image, Point, Cv2Matrix
from pathlib import Path

import cv2

def tranformPoint(p: Point, matrix: Cv2Matrix) -> Point:
    px = (matrix[0][0]*p[0] + matrix[0][1]*p[1] + matrix[0][2]) / ((matrix[2][0]*p[0] + matrix[2][1]*p[1] + matrix[2][2]))
    py = (matrix[1][0]*p[0] + matrix[1][1]*p[1] + matrix[1][2]) / ((matrix[2][0]*p[0] + matrix[2][1]*p[1] + matrix[2][2]))
    return (int(px), int(py))

def transformRect(r: CellRect, matrix: Cv2Matrix) -> CellRect:
    points = []
    for p in r:
        points.append(tranformPoint(p,matrix))
    return CellRect(points)

def updateRects(rects: list[CellRect], matrix: Cv2Matrix):
    for i,rect in enumerate(rects):
        rects[i] = transformRect(rect,matrix)

def extractData(imagepath: Path) -> tuple[Cv2Image,CrossWordData]:
    if not imagepath.is_file():
        raise Exception(f"Error while reading image file: cannot find file \'{imagepath}\'")
    image = cv2.imread(str(imagepath))
    if image is None:
        raise Exception(f"Error while reading image file: file type \'{imagepath.suffix}\' not supported")
    
    rects = CellRectExtr.getCellRects(image.copy())
    scanned, matrix = Scan.scan(image, rects)
    updateRects(rects,matrix)
    data = CellsDataExtr.extractCellsData(scanned,rects)
    return scanned, data
    