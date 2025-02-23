from . import ImageProcessing as ImgProc
from ..Utility import GeometricCalculation as GeomCalc
from ..SingleCellData import CellRect
from ..Type import Cv2Image,Cv2Contour

import cv2
import numpy as np
import shapely.geometry
    
def getCellRects(img: Cv2Image) -> list[CellRect]:
    processed = ImgProc.preProcessImage(img.copy())

    contours, hierarchy = cv2.findContours(processed, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

    closed_cell_contours = _filterClosedContours(list(contours), hierarchy)
    
    rects = _contoursToRects(closed_cell_contours)

    neighboredrects = _filterNeighboringRects(rects)

    nonparentrects = _filterNonParentRects(neighboredrects)

    return nonparentrects

def _filterClosedContours(contours: list[Cv2Contour], hierarchy) -> list[Cv2Contour]:
    closed = []
    for i, cnt in enumerate(contours):
        if hierarchy[0][i][3] == -1:
            continue
        area = cv2.contourArea(cnt)
        if area > cv2.arcLength(cnt, True) and area > 500:
            closed.append(cnt)
    return closed

def _contoursToRects(contours: list[Cv2Contour]) -> list[CellRect]:
    # filter Quadrillaterals and Rhombus
    filteredrects: list[CellRect] = []
    nonfilteredcontours = []
    for contour in contours:
        rect = CellRect(contour.squeeze())
        if _contourIsQuadrillateral(rect,contour) and rect.isRhombus():
            filteredrects.append(rect)
        else:
            nonfilteredcontours.append(contour)

    if len(nonfilteredcontours) == 0:
        return filteredrects

    # merge possible non filtered contours
    avoidindexes: list[int] = []
    for i, nfcnt in enumerate(nonfilteredcontours):
        if i in avoidindexes:
            continue
        hull1 = cv2.convexHull(nfcnt)
        area1 = cv2.contourArea(hull1)
        points1 = [(p[0][0],p[0][1]) for p in nfcnt]
        hullpoints1 = [(p[0][0],p[0][1]) for p in hull1]
        polygon1 = shapely.geometry.Polygon(hullpoints1)
        for j in range(i+1,len(nonfilteredcontours)):
            if j in avoidindexes:
                continue
            
            # merge contours
            hull2 = cv2.convexHull(nonfilteredcontours[j])
            area2 = cv2.contourArea(hull2)
            points2 = [(p[0][0],p[0][1]) for p in nonfilteredcontours[j]]
            hullpoints2 = [(p[0][0],p[0][1]) for p in hull2]
            polygon2 = shapely.geometry.Polygon(hullpoints2)
            contour = np.array(points1+points2).reshape((-1,1,2)).astype(np.int32)
            hull = cv2.convexHull(contour)
            
            # calc merged area
            totalarea = cv2.contourArea(hull)
            overlaparea = polygon1.intersection(polygon2).area
            addedarea = area1+area2-overlaparea

            # check if area is same
            factor = 0.03
            if addedarea <= totalarea * (1+factor) and addedarea >= totalarea * (1-factor):
                mergedrect = CellRect(hull.squeeze())

                # filter Quadrillateral and Rhombus
                if _contourIsQuadrillateral(mergedrect,hull) and mergedrect.isRhombus():

                    # filter rect with neighbors
                    mergedlength = mergedrect.meanSideLength()
                    hasneighbor = False
                    distfactor = 0.2
                    mergedcenter = mergedrect.center()
                    for filteredrect in filteredrects:
                        center = filteredrect.center()
                        dist = GeomCalc.distBetweenPoints(center,mergedcenter)
                        if dist > mergedlength * (1+distfactor) or dist < mergedlength * (1-distfactor):
                            hasneighbor = True
                            break
                    if hasneighbor:
                        filteredrects.append(mergedrect)
                        avoidindexes.append(j)
    return filteredrects

def _filterNonParentRects(rects: list[CellRect]) -> list[CellRect]:
    filteredrects: list[CellRect] = []
    rectsdata: list[dict] = []
    for rect in rects:
        rectsdata.append({
            "Rect": rect,
            "Area": rect.area(),
            "Center": rect.center()
        })
    for i in range(len(rectsdata)):
        hasinner = False
        for j in range(len(rectsdata)):
            if i != j:
                if (rectsdata[i]["Rect"].pointInside(rectsdata[j]["Center"]) and
                    rectsdata[j]["Area"] < rectsdata[i]["Area"]):
                    hasinner = True
                    break
        if not hasinner:
            filteredrects.append(rectsdata[i]["Rect"])
    return filteredrects

def _contourIsQuadrillateral(rect: CellRect, contour: Cv2Contour) -> bool:
    rectarea = rect.area()
    hull = cv2.convexHull(contour)
    factor = 0.05
    indexes = [i for p in rect for i in range(len(hull)) if hull[i][0][0] == p[0] and hull[i][0][1] == p[1]]
    for i in range(len(indexes)):
        first = indexes[i]
        second = indexes[(i+1)%len(indexes)]
        area = 0
        if first < second:
            arc1 = hull[first:second+1]
            arc2 = np.concatenate((hull[second:],hull[:first+1]),axis=0)
            length1 = cv2.arcLength(arc1,closed=False)
            length2 = cv2.arcLength(arc2,closed=False)
            if length1 < length2:
                area = cv2.contourArea(arc1)
            else:
                area = cv2.contourArea(arc2)
        else:
            arc1 = hull[second:first+1]
            arc2 = np.concatenate((hull[first:],hull[:second+1]),axis=0)
            length1 = cv2.arcLength(arc1,closed=False)
            length2 = cv2.arcLength(arc2,closed=False)
            if length1 < length2:
                area = cv2.contourArea(arc1)
            else:
                area = cv2.contourArea(arc2)
        
        if area > rectarea * (factor):
            return False
    return True

def _filterNeighboringRects(rects: list[CellRect]) -> list[CellRect]:
    celldata: list[dict] = []
    for r in rects:
        celldata.append({
            "Rect" : r,
            "Center" : r.center(),
            "SideLength" : r.meanSideLength()
        })

    filteredrects = []
    distfactor = 0.2
    sizefactor = 0.05

    for i in range(len(celldata)):
        for j in range(len(celldata)):
            if i == j:
                continue
            dist = GeomCalc.distBetweenPoints(celldata[i]["Center"],celldata[j]["Center"])
            if (dist <= celldata[i]["SideLength"] * (1+distfactor) and dist >= celldata[i]["SideLength"] * (1-distfactor) and
                celldata[i]["SideLength"] <= celldata[j]["SideLength"] * (1+sizefactor) and celldata[i]["SideLength"] >= celldata[j]["SideLength"] * (1-sizefactor)):
                filteredrects.append(celldata[i]["Rect"])
                break
    return filteredrects
