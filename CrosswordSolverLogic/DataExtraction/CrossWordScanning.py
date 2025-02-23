from ..Utility import GeometricCalculation as GeomCalc
from ..Utility import ImageWarping as ImgWp
from ..SingleCellData import CellRect
from ..Type import Point,Line,Cv2Image,Cv2Matrix, Cv2Contour

import cv2
import numpy as np

def scan(img: Cv2Image, rects: list[CellRect]) -> tuple[Cv2Image,Cv2Matrix]:
    totalrect = _totalRect(rects)
    warpedimg, matrix = ImgWp.warpRectWithMatrix(img.copy(),totalrect)
    return warpedimg, matrix

def _totalRect(rects: list[CellRect]) -> CellRect:
    hull = _rectsToHull(rects)
    hulllines = _contourToLines(hull)
    outerrects = _getOuterRects(rects,hulllines)
    dirvectors = _getDirectionVectors(outerrects)
    lines = []
    for i in range(4):
        outmost = _getOutMostPoint(_concatRectPoints(outerrects[i]),dirvectors[i])
        line = (outmost,np.array(outmost) + np.array(dirvectors[i]))
        lines.append(line)

    topleft = GeomCalc.lineIntersection(lines[3],lines[0])
    bottomleft = GeomCalc.lineIntersection(lines[0],lines[1])
    bottomright = GeomCalc.lineIntersection(lines[1],lines[2])
    topright = GeomCalc.lineIntersection(lines[2],lines[3])

    return CellRect([topleft,bottomleft,bottomright,topright])

def _concatRectPoints(rects: list[CellRect]) -> list[Point]:
    points = []
    for rect in rects:
        a,b,c,d = rect
        points += [a,b,c,d] 
    return points

def _rectsToHull(rects: list[CellRect]):
    contour = np.full((len(rects*4), 1,2), 0)
    index = 0
    for rect in rects:
        for p in rect:
            np.put(contour[index][0],0,p[0])
            np.put(contour[index][0],1,p[1])
            index += 1
    hull = cv2.convexHull(contour)
    return hull

def _contourToLines(contour: Cv2Contour) -> list[Line]:
    lines: list[Line] = []
    points = contour.squeeze()
    for i in range(len(points)-1):
        a = (int(points[i][0]),int(points[i][1]))
        b =  (int(points[i+1][0]),int(points[i+1][1]))
        lines.append((a,b))
    a = (points[len(points)-1][0],points[len(points)-1][1])
    b =  (points[0][0],points[0][1])
    lines.append((a,b))
    return lines

def _similarAngles(angle1: float, angle2: float, tolerance: float) -> bool:
    angle1 = angle1 % 360
    angle2 = angle2 % 360
    diff1 = abs(angle1 - angle2)
    diff2 = min(angle1,angle2) + (360-max(angle1,angle2))
    if diff1 <= 180 + tolerance and diff1 >= 180 - tolerance:
        return True
    elif diff2 <= 180 + tolerance and diff2 >= 180 - tolerance:
        return True
    else:
        return False

def _getOuterRects(rects: list[CellRect], hulllines: list[Line]) -> list[list[CellRect]]:
    count = 4
    result: list[list[CellRect]] = []
    for i in range(count):
        sidelines = [(rect[i],rect[(i+1)%count]) for rect in rects]
        outerrects = []
        for j in range(len(sidelines)):
            sline = sidelines[j]
            slineangle = np.degrees(np.arctan2(sline[0][1]-sline[1][1],sline[0][0]-sline[1][0]))
            slinelength = GeomCalc.distBetweenPoints(sline[0],sline[1])
            for hline in hulllines:
                hlineangle = np.degrees(np.arctan2(hline[0][1]-hline[1][1],hline[0][0]-hline[1][0]))
                near = False
                for p in sline:
                    if GeomCalc.pointDistToLine(hline[0],hline[1],p) <= slinelength * 0.2:
                        near = True
                if _similarAngles(hlineangle, slineangle,5) and near:
                    outerrects.append(rects[j])
                    break
        result.append(outerrects)
    return result

def _getOutMostPoint(points: list[Point], dirvector: Point) -> Point:
    lp1 = points[0]
    lp2 = np.array(lp1) + np.array(dirvector)
    lp2 = (lp1[0]+dirvector[0],lp1[1]+dirvector[1])
    crosses = []
    for p in points:
        crosses.append(GeomCalc.crossProduct(lp1,lp2,p))
    maxindx = np.argmax(np.array(crosses))

    orth = (-dirvector[1],dirvector[0])
    norm = np.linalg.norm(orth)
    normorth = (orth[0]/norm,orth[1]/norm)
    lengthorth = (int(normorth[0]*10),int(normorth[1]*10))

    return (points[maxindx][0]+lengthorth[0],points[maxindx][1]+lengthorth[1])

def _getDirectionVectors(outerrects: list[list[CellRect]]) -> list[Point]:
    vectors = []
    for i in range(len(outerrects)):
        sidx = (i+1)%len(outerrects)
        meandir = (sum([r[sidx][0]-r[i][0] for r in outerrects[i]]),sum([r[sidx][1]-r[i][1] for r in outerrects[i]]))
        sortedrects = sorted(outerrects[i],key=lambda r: np.dot(r.center(),meandir))
        vector = (0,0)
        for j in range(len(sortedrects)):
            dir = (sortedrects[j][sidx][0]-sortedrects[j][i][0],sortedrects[j][sidx][1]-sortedrects[j][i][1])
            vector = np.array(vector) + np.array(dir)
            if j != len(sortedrects)-1:
                disttonext = GeomCalc.distBetweenPoints(sortedrects[j].center(),sortedrects[j+1].center())
                length = sortedrects[j].meanSideLength()
                factor = 0.1
                if disttonext <= length *(1+factor) and disttonext >= length *(1-factor):
                    connecteddir = (sortedrects[j+1][i][0]-sortedrects[j][sidx][0],sortedrects[j+1][i][1]-sortedrects[j][sidx][1])
                    vector = np.array(vector) + np.array(connecteddir)

        vectors.append(vector)
    return vectors
