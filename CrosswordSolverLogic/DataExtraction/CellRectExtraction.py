from . import ImageProcessing as ImgProc
from ..Utility import GeometricCalculation as GeomCalc
from ..SingleCellData import CellRect
from ..Type import Cv2Image,Cv2Contour

import cv2
import numpy as np
import shapely.geometry

def getCellRects(img: Cv2Image) -> list[CellRect]:
    roughrects = _getRoughCellRects(img)
    cellsize = _getCellSize(roughrects)
    celldist = _getCellDistance(roughrects,cellsize)

    cellsize = (cellsize+celldist) / 28 * 27
    factor = 166 / cellsize
    cellsize *=factor
    newheight = int(factor * img.shape[0])
    newwidth = int(factor * img.shape[1])
    resizedimg = cv2.resize(img,(newwidth,newheight))

    preciserects = _getPreciseCellRects(resizedimg,cellsize)

    _resizeCellRects(preciserects,factor)

    return preciserects

def _getRoughCellRects(img: Cv2Image) -> list[CellRect]:
    processed = ImgProc.prePreProcessGrid(img.copy())

    contours, hierarchy = cv2.findContours(processed, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

    closed_cell_contours = _filterClosedContours(list(contours), hierarchy)
    
    rects,_ = _perfectContoursToRects(closed_cell_contours)

    neighboredrects = _filterNeighboringRects(rects)

    nonparentrects = _filterNonParentRects(neighboredrects)

    return nonparentrects

def _getPreciseCellRects(img: Cv2Image, cellsize: float) -> list[CellRect]:
    processed = ImgProc.preProcessGrid(img.copy())

    contours, hierarchy = cv2.findContours(processed, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

    closed_cell_contours = _filterClosedContoursPrecise(list(contours), hierarchy, cellsize)
    
    rects,nonfilteredcontours = _perfectContoursToRects(closed_cell_contours)
    mergedrects = _mergeContoursToRects(rects,nonfilteredcontours, cellsize)
    totalrects = rects+mergedrects

    neighboredrects = _filterNeighboringRects(totalrects)

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

def _filterClosedContoursPrecise(contours: list[Cv2Contour], hierarchy, cellsize: float) -> list[Cv2Contour]:
    closed = []
    cellarea = cellsize**2
    minarea = cellarea / 20
    maxarea = cellarea *2
    for i, cnt in enumerate(contours):
        if hierarchy[0][i][3] == -1:
            continue
        area = cv2.contourArea(cnt)
        if area > cv2.arcLength(cnt, True) and area >= minarea and area <= maxarea:
            closed.append(cnt)
    return closed

def _perfectContoursToRects(contours: list[Cv2Contour]) -> tuple[list[CellRect],list[Cv2Contour]]:
    filteredrects: list[CellRect] = []
    nonfilteredcontours = []
    for contour in contours:
        rect = CellRect(contour.squeeze())
        if _contourIsQuadrillateral(rect,contour) and rect.isRhombus():
            filteredrects.append(rect)
        else:
            nonfilteredcontours.append(contour)
    return filteredrects, nonfilteredcontours

def _mergeContoursToRects(rects: list[CellRect],contours: list[Cv2Contour], cellsize: float):
    mergedrects = []
    avoidindexes: list[int] = []
    for i, nfcnt in enumerate(contours):
        if i in avoidindexes:
            continue
        hull1 = cv2.convexHull(nfcnt)
        area1 = cv2.contourArea(hull1)
        points1 = [(p[0][0],p[0][1]) for p in nfcnt]
        hullpoints1 = [(p[0][0],p[0][1]) for p in hull1]
        polygon1 = shapely.geometry.Polygon(hullpoints1)
        for j in range(i+1,len(contours)):
            if j in avoidindexes:
                continue
            # merge contours
            hull2 = cv2.convexHull(contours[j])
            area2 = cv2.contourArea(hull2)
            points2 = [(p[0][0],p[0][1]) for p in contours[j]]
            hullpoints2 = [(p[0][0],p[0][1]) for p in hull2]
            polygon2 = shapely.geometry.Polygon(hullpoints2)
            contour = np.array(points1+points2).reshape((-1,1,2)).astype(np.int32)
            hull = cv2.convexHull(contour)
            
            # calc merged area
            totalarea = cv2.contourArea(hull)
            overlaparea = polygon1.intersection(polygon2).area
            addedarea = area1+area2-overlaparea

            # check if area is same
            factor = 0.04
            if addedarea <= totalarea * (1+factor) and addedarea >= totalarea * (1-factor):
                mergedrect = CellRect(hull.squeeze())
                # filter Quadrillateral and Rhombus
                if _contourIsQuadrillateral(mergedrect,hull) and mergedrect.isRhombus():
                    
                    # filter rect with neighbors
                    mergedlength = mergedrect.meanSideLength()
                    hasneighbor = False
                    distfactor = 0.2
                    mergedcenter = mergedrect.center()
                    for filteredrect in rects:
                        center = filteredrect.center()
                        dist = GeomCalc.distBetweenPoints(center,mergedcenter)
                        if dist > mergedlength * (1+distfactor) or dist < mergedlength * (1-distfactor):
                            hasneighbor = True
                            break
                    if hasneighbor:
                        mergedrects.append(mergedrect)
                        avoidindexes.append(j)
    return mergedrects

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

def _getCellSize(rects: list[CellRect]) -> float:
    allcellsize = 0
    for r in rects:
        l1 = GeomCalc.distBetweenPoints(r[0],r[1])
        l2 = GeomCalc.distBetweenPoints(r[1],r[2])
        l3 = GeomCalc.distBetweenPoints(r[2],r[3])
        l4 = GeomCalc.distBetweenPoints(r[3],r[0])
        allcellsize += (l1+l2+l3+l4)/4
    return allcellsize/len(rects)

def _getCellDistance(rects: list[CellRect], cellsize: float) -> float:
    maxdist = cellsize/4
    dists = []
    for r in rects:
        for p in r:
            for r2 in rects:
                if r != r2:
                    for p2 in r2:
                        dist = GeomCalc.distBetweenPoints(p,p2)
                        if dist <= maxdist:
                            dists.append(dist)
    dists = set(dists)
    return sum(dists)/len(dists)

def _resizeCellRects(rects: list[CellRect], factor: float):
    for i in range(len(rects)):
        for j in range(4):
            rects[i][j] = (int(rects[i][j][0]/factor),int(rects[i][j][1]/factor))