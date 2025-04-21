from ..Utility import GeometricCalculation as GeomCalc
from ..Type import Cv2Image, Cv2Contour, Triangle, Point
from ..SingleCellData import ArrowsData, ArrowData
from . import ImageProcessing as ImgProc

import numpy as np
import cv2

def getArrows(img: Cv2Image) -> tuple[list[Cv2Contour], ArrowsData]:
    allcontours = []
    allarrows = []
    arrowimg = ImgProc.preProcessArrowCell(img.copy())
    arrowheadimg = ImgProc.preProcessArrowHeadCell(img.copy())
    bigcontour, circlearrows = _getCircleArrows(arrowimg, arrowheadimg)
    if bigcontour is not None:
        allcontours.append(bigcontour)
        allarrows.extend(circlearrows)
    else:
        smallcontours, smallarrows = _getSmallArrows(arrowimg, arrowheadimg)
        longcontours, longarrows = _getLongArrows(arrowimg, arrowheadimg)
        allcontours.extend(smallcontours)
        allcontours.extend(longcontours)
        allarrows.extend(smallarrows)
        allarrows.extend(longarrows)
    return allcontours, allarrows

def _getCircleArrows(arrowimg: Cv2Image, arrowheadimg: Cv2Image) -> tuple[Cv2Contour | None, ArrowsData]:
    biggestcnt = _getBigCircleContour(arrowimg)
    if biggestcnt is None:
        return None,[]
    onlybigimg = ImgProc.fillBackgroundBlack(arrowimg.copy(),[biggestcnt])
    onlybigheadimg = ImgProc.fillBackgroundBlack(arrowheadimg.copy(),[biggestcnt])
    headcontours, _ = cv2.findContours(onlybigheadimg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    borderwidth = 7
    arrows = []

    for cnt in headcontours:
        triangle = _contourToTriangle(onlybigheadimg,cnt)
        if triangle is None:
            continue
        center = GeomCalc.centerOfTriangle(triangle)
        if _arrrowDown(triangle):
            long = center[1] >= arrowimg.shape[0] * 0.15
            if long:
                miny = min(p[1] for p in triangle)
                cut = onlybigimg.copy()
                cut[miny:,:] = 0
                cut = ImgProc.drawBorder(cut,(0,0,0),borderwidth)
                orgcntcut = _getBiggestContour(cut)

                if orgcntcut is not None:
                    arrowdata = _getLongArrowData(cut,orgcntcut,(0,1),center)
                    arrows.append(arrowdata)
            else:
                position = sum(x for x,y in triangle)/len(triangle)/arrowimg.shape[1]
                arrows.append(ArrowData((0,-1),(0,1),position))
        elif _arrrowRight(triangle):
            long = center[0] >= arrowimg.shape[1] * 0.15
            if long:
                minx = min(p[0] for p in triangle)
                cut = onlybigimg.copy()
                cut[:,minx:] = 0
                cut = ImgProc.drawBorder(cut,(0,0,0),borderwidth)
                orgcntcut = _getBiggestContour(cut)

                if orgcntcut is not None:
                    arrowdata = _getLongArrowData(cut,orgcntcut,(1,0),center)
                    arrows.append(arrowdata)
            else:
                position = sum(y for x,y in triangle)/len(triangle)/arrowimg.shape[0]
                arrows.append(ArrowData((-1,0),(1,0),position))
    return biggestcnt, arrows

def _getSmallArrows(arrowimg: Cv2Image, arrowheadimg: Cv2Image) -> tuple[list[Cv2Contour], ArrowsData]:
    arrowcontours = []
    arrows = []
    contours, _ = cv2.findContours(arrowimg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    headcontours, _ = cv2.findContours(arrowheadimg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    foundtop = False
    foundleft = False
    for cnt in headcontours:
        triangle = _contourToTriangle(arrowheadimg,cnt)
        if triangle is None:
            continue
        orgcnt = _getOriginalContour(triangle,list(contours))
        if orgcnt is None:
            continue

        center = GeomCalc.centerOfTriangle(triangle)
        if _arrrowDown(triangle):
            if center[1] >= arrowimg.shape[0] * 0.15:
                continue
            if foundtop:
                raise Exception("Error while extracting arrow data: found two small arrows pointing downwards")
            position = sum(x for x,y in triangle)/len(triangle)/arrowimg.shape[1]
            arrows.append(ArrowData((0,-1),(0,1),position))
            arrowcontours.append(orgcnt)
            foundtop = True

        if _arrrowRight(triangle):
            if center[0] >= arrowimg.shape[1] * 0.15:
                continue
            if foundleft:
                raise Exception("Error while extracting arrow data: found two small arrows pointing to the right")
            position = sum(y for x,y in triangle)/len(triangle)/arrowimg.shape[0]
            arrows.append(ArrowData((-1,0),(1,0),position))
            arrowcontours.append(orgcnt)
            foundleft = True
    
    return arrowcontours, arrows

def _getLongArrows(arrowimg: Cv2Image, arrowheadimg: Cv2Image) -> tuple[list[Cv2Contour], ArrowsData]:
    arrowcontours = []
    arrows = []
    contours, _ = cv2.findContours(arrowimg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    headcontours, _ = cv2.findContours(arrowheadimg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    borderwidth = 7
    h,w = arrowimg.shape[:2]

    foundtop = False
    foundleft = False
    for cnt in headcontours:
        triangle = _contourToTriangle(arrowheadimg,cnt)
        if triangle is None:
            continue
        orgcnt = _getOriginalContour(triangle,list(contours))
        if orgcnt is None:
            continue

        mask = np.ones_like(arrowimg) * 0
        cv2.drawContours(mask, [orgcnt], -1, (255, 255, 255),-1, cv2.LINE_AA) # type: ignore
        mask = ImgProc.drawBorder(mask,(0,0,0),borderwidth)

        center = GeomCalc.centerOfTriangle(triangle)
        if _arrrowDown(triangle):
            if center[1] < arrowimg.shape[0] * 0.15:
                continue
            miny = min(p[1] for p in triangle)
            cut = mask.copy()
            cut[miny:,:] = 0
            bigcnt = _getBiggestContour(cut)
            if bigcnt is None:
                continue
            arrowdata = _getLongArrowData(arrowimg,bigcnt,(0,1),center)
            if arrowdata:
                if foundtop:
                    raise Exception("Error while extracting arrow data: found two long arrows pointing downwards")
                arrows.append(arrowdata)
                arrowcontours.append(orgcnt)
                foundtop = True
            
        if _arrrowRight(triangle):
            if center[0] < arrowimg.shape[1] * 0.15:
                continue
            minx = min(p[0] for p in triangle)
            cut = mask.copy()
            cut[:,minx:] = 0
            bigcnt = _getBiggestContour(cut)
            if bigcnt is None:
                continue
            arrowdata = _getLongArrowData(arrowimg,bigcnt,(1,0),center)
            if arrowdata:
                if foundleft:
                    raise Exception("Error while extracting arrow data: found two long arrows pointing to the right")
                arrows.append(arrowdata)
                arrowcontours.append(orgcnt)
                foundleft = True
    return arrowcontours, arrows

def _getOriginalContour(triangle: Triangle, contours: list[Cv2Contour]) -> Cv2Contour | None:
    center = GeomCalc.centerOfTriangle(triangle)
    for c in contours:
        if cv2.pointPolygonTest(c,center,False) == 1:
            return c
    return None

def _contourToTriangle(img: Cv2Image, contour: Cv2Contour) -> Triangle | None:
    epsi = img.shape[0]*4 * 0.005
    approx = cv2.approxPolyDP(contour, epsi, True)
    if len(approx) < 3:
        return None
    corners = list(approx.squeeze().tolist())
    while True:
        found = False
        for i in range(len(corners)):
            pt0 = corners[(i-1)%len(corners)]
            pt1 = corners[i]
            pt2 = corners[(i+1)%len(corners)]
            ang = GeomCalc.angle(pt0, pt2, pt1)
            if ang > 100:
                corners = corners[:i] + corners[i+1:]
                found = True
                break
        if len(corners) < 3:
            return None
        if not found:
            break
    
    hull = cv2.convexHull(contour)
    hullarea = cv2.contourArea(hull)
    cntarea = cv2.contourArea(contour)
    if cntarea < hullarea * 0.7:
        return None
    
    maxarea = 0
    maxtriangle: Triangle | None = None
    for i in range(len(corners)-2):
        for j in range(i+1,len(corners)-1):
            for k in range(j+1,len(corners)):
                triangle = Triangle([corners[i],corners[j],corners[k]])
                triarea = GeomCalc.polygonArea(list(triangle))
                if triarea >= hullarea * 0.6 and triarea > maxarea:
                    maxtriangle = triangle

    return maxtriangle

def _getLongArrowData(img: Cv2Image, contour: Cv2Contour, direction: Point, arrowcenter: Point) -> ArrowData | None:
    points = contour.squeeze()
    furthest_point = max(points,key=lambda p: GeomCalc.distBetweenPoints(p,arrowcenter))
    max_ydist = img.shape[0]-furthest_point[1]
    max_xdist = img.shape[1]-furthest_point[0]
    min_ydist = furthest_point[1]
    min_xdist = furthest_point[0]
    min_dist = min([max_ydist,max_xdist,min_ydist,min_xdist])

    if direction == (0,1):
        if min_dist == min_ydist:
            if furthest_point[0]/img.shape[1] < 0.5:
                return ArrowData((-1,-1),direction,-1)
            else:
                return ArrowData((1,-1),direction,-1)
        if min_dist == min_xdist:
            return ArrowData((-1,0),direction, furthest_point[1]/img.shape[0])
        if min_dist == max_xdist:
            return ArrowData((1,0),direction, furthest_point[1]/img.shape[0])
    elif direction == (1,0):
        if min_dist == min_xdist:
            if furthest_point[1]/img.shape[0] < 0.5:
                return ArrowData((-1,-1),direction,-1)
            else:
                return ArrowData((-1,1),direction,-1)
        if min_dist == min_ydist:
            return ArrowData((0,-1),direction, furthest_point[0]/img.shape[1])
        if min_dist == max_ydist:
            return ArrowData((0,1),direction, furthest_point[0]/img.shape[1])
    return None

def _arrrowDown(triangle: Triangle) -> bool:
    sorttop = sorted(triangle, key=lambda p : p[1])
    t1 = sorttop[0]
    t2 = sorttop[1]
    if abs(t1[1]-t2[1]) > abs(t1[0]-t2[0]) * 0.2:
        return False
    left = min(sorttop[:2], key=lambda p : p[0])
    right = max(sorttop[:2], key=lambda p : p[0])
    p3 = sorttop[2]
    if p3[0] <= left[0] or p3[0] >= right[0]:
        return False
    return True

def _arrrowRight(triangle: Triangle) -> bool:
    sortleft = sorted(triangle, key=lambda p : p[0])
    l1 = sortleft[0]
    l2 = sortleft[1]
    if abs(l1[0]-l2[0]) > abs(l1[1]-l2[1]) * 0.2:
        return False
    
    top = min(sortleft[:2], key=lambda p : p[1])
    down = max(sortleft[:2], key=lambda p : p[1])
    p3 = sortleft[2]
    if p3[1] <= top[1] or p3[1] >= down[1]:
        return False
    return True 

def _getBigCircleContour(img: Cv2Image) -> Cv2Contour | None:
    imgarea = img.shape[0]*img.shape[1]
    biggestcnt = _getBiggestContour(img)
    if biggestcnt is None:
        return None
    hull = cv2.convexHull(biggestcnt) # type: ignore
    area = cv2.contourArea(hull)
    if area <= imgarea*0.5:
        return None
    return biggestcnt

def _getBiggestContour(img: Cv2Image) -> Cv2Contour | None:
    contours, _ = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if len(contours) == 0:
        return None
    biggestcnt = max(contours, key=lambda c : cv2.contourArea(c))
    return biggestcnt