from ..Utility import GeometricCalculation as GeomCalc
from ..Type import Cv2Image, Cv2Contour, Triangle, Point
from ..SingleCellData import ArrowsData, ArrowData
from . import ImageProcessing as ImgProc

import cv2

def getArrows(img: Cv2Image) -> tuple[list[Cv2Contour], ArrowsData]:
    allcontours = []
    allarrows = []
    arrowimg = ImgProc.preProcessArrowCell(img.copy())
    arrowheadimg = ImgProc.preProcessArrowHeadCell(img.copy())
    bigcontour, circlearrows = _getCircleArrows(arrowimg, arrowheadimg)
    if bigcontour is not None:
        arrowimg = ImgProc.fillContoursBlack(arrowimg,[bigcontour])
        arrowheadimg = ImgProc.fillContoursBlack(arrowheadimg,[bigcontour])
        allcontours.append(bigcontour)
    smallcontours, smallarrows = _getSmallArrows(arrowimg, arrowheadimg)
    longcontours, longarrows = _getLongArrows(arrowimg, arrowheadimg)
    allcontours.extend(smallcontours)
    allcontours.extend(longcontours)
    allarrows.extend(circlearrows)
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

    arrows = []

    for cnt in headcontours:
        triangle = _contourToTriangle(onlybigheadimg,cnt)
        if triangle is None:
            continue
        center = GeomCalc.centerOfTriangle(triangle)
        if _arrrowDown(triangle):
            long = center[1] >= arrowimg.shape[0] * 0.15
            if long:
                minx = min(p[0] for p in triangle)
                cut = onlybigimg.copy()
                cut[:,minx+1:] = 0
                bigcnt = _getBiggestContour(cut)
                if bigcnt is not None:
                    arrowdata = _getLongArrowData(cut,bigcnt,(0,1))
                    arrows.append(arrowdata)
            else:
                position = sum(x for x,y in triangle)/len(triangle)/arrowimg.shape[1]
                arrows.append(ArrowData((0,-1),(0,1),position))
        elif _arrrowRight(triangle):
            long = center[0] >= arrowimg.shape[1] * 0.15
            if long:
                miny = min(p[1] for p in triangle)
                cut = onlybigimg.copy()
                cut[miny+1:,:] = 0
                bigcnt = _getBiggestContour(cut)
                if bigcnt is not None:
                    arrowdata = _getLongArrowData(cut,bigcnt,(1,0))
                    arrows.append(arrowdata)
            else:
                position = sum(y for x,y in triangle)/len(triangle)/arrowimg.shape[0]
                arrows.append(ArrowData((-1,0),(1,0),position))

    return biggestcnt, arrows

def _getSmallArrows(arrowimg: Cv2Image, arrowheadimg: Cv2Image) -> tuple[list[Cv2Contour], ArrowsData]:
    contours = []
    arrows = []
    headcontours, _ = cv2.findContours(arrowheadimg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    foundtop = False
    top = _getDownSmallArrowImage(arrowimg)
    contourstop, _ = cv2.findContours(top, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in headcontours:
        triangle = _contourToTriangle(top,cnt)
        if triangle is None or not _arrrowDown(triangle):
            continue

        center = GeomCalc.centerOfTriangle(triangle)
        if center[1] >= arrowimg.shape[0] * 0.15:
            continue

        orgcnt = _getOriginalContour(triangle,list(contourstop))
        if orgcnt is None:
            continue
        
        if foundtop:
            raise Exception("Error while extracting arrow data: found two small arrows pointing downwards")

        position = sum(x for x,y in triangle)/len(triangle)/arrowimg.shape[1]
        arrows.append(ArrowData((0,-1),(0,1),position))
        contours.append(orgcnt)
        foundtop = True

    foundleft = False
    left = _getLeftSmallArrowImage(arrowimg)
    contoursleft, _ = cv2.findContours(left, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in headcontours:
        triangle = _contourToTriangle(top,cnt)
        if triangle is None or not _arrrowRight(triangle):
            continue

        center = GeomCalc.centerOfTriangle(triangle)
        if center[0] >= arrowimg.shape[1] * 0.15:
            continue

        orgcnt = _getOriginalContour(triangle,list(contoursleft))
        if orgcnt is None:
            continue
        
        if foundleft:
            raise Exception("Error while extracting arrow data: found two small arrows pointing to the right")

        position = sum(y for x,y in triangle)/len(triangle)/arrowimg.shape[0]
        arrows.append(ArrowData((-1,0),(1,0),position))
        contours.append(orgcnt)
        foundleft = True
    
    return contours, arrows

def _getLongArrows(arrowimg: Cv2Image, arrowheadimg: Cv2Image) -> tuple[list[Cv2Contour], ArrowsData]:
    arrowcontours = []
    arrows = []
    contours, _ = cv2.findContours(arrowimg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    foundtop = False
    top = _getDownLongArrowImage(arrowheadimg)
    contourstop, _ = cv2.findContours(top, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contourstop:
        triangle = _contourToTriangle(top,cnt)
        if triangle is None or not _arrrowDown(triangle):
            continue

        center = GeomCalc.centerOfTriangle(triangle)
        if center[1] < arrowimg.shape[0] * 0.15:
            continue

        orgcnt = _getOriginalContour(triangle,list(contours))
        if orgcnt is None:
            continue
        

        arrowdata = _getLongArrowData(arrowimg,orgcnt,(0,1))
        if arrowdata:
            if foundtop:
                raise Exception("Error while extracting arrow data: found two long arrows pointing downwards")

            arrows.append(arrowdata)
            arrowcontours.append(orgcnt)
            foundtop = True
    
    foundleft = False
    left = _getLeftLongArrowImage(arrowheadimg)
    contoursleft, _ = cv2.findContours(left, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contoursleft:
        triangle = _contourToTriangle(top,cnt)
        if triangle is None or not _arrrowRight(triangle):
            continue

        center = GeomCalc.centerOfTriangle(triangle)
        if center[0] < arrowimg.shape[1] * 0.15:
            continue

        orgcnt = _getOriginalContour(triangle,list(contours))
        if orgcnt is None:
            continue

        arrowdata = _getLongArrowData(arrowimg,orgcnt,(1,0))
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

def _getDownSmallArrowImage(img: Cv2Image) -> Cv2Image:
    h,w = img.shape[:2]
    contours, _ = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    wrongcontours = []
    for cnt in contours:
        inside = True
        for p in cnt:
            x,y = p[0]
            if x < w*0.35 or x > w*0.65 or y > h*0.3:
                inside = False
                break
        if not inside:
            wrongcontours.append(cnt)
    return ImgProc.fillContours(img.copy(),wrongcontours,(0,0,0))

def _getLeftSmallArrowImage(img: Cv2Image) -> Cv2Image:
    h,w = img.shape[:2]
    contours, _ = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    wrongcontours = []
    for cnt in contours:
        inside = True
        for p in cnt:
            x,y = p[0]
            if x > w*0.3:
                inside = False
                break
        if not inside:
            wrongcontours.append(cnt)
    return ImgProc.fillContours(img.copy(),wrongcontours,(0,0,0))

def _getDownLongArrowImage(img: Cv2Image) -> Cv2Image:
    h,w = img.shape[:2]
    contours, _ = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    wrongcontours = []
    for cnt in contours:
        inside = True
        for p in cnt:
            x,y = p[0]
            if x < w*0.35 or x > w*0.65 or y > h*0.5:
                inside = False
                break
        if not inside:
            wrongcontours.append(cnt)
    return ImgProc.fillContours(img.copy(),wrongcontours,(0,0,0))

def _getLeftLongArrowImage(img: Cv2Image) -> Cv2Image:
    h,w = img.shape[:2]
    contours, _ = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    wrongcontours = []
    for cnt in contours:
        inside = True
        for p in cnt:
            x,y = p[0]
            if y < h*0.35 or y > h*0.65 or x > w*0.5:
                inside = False
                break
        if not inside:
            wrongcontours.append(cnt)
    return ImgProc.fillContours(img.copy(),wrongcontours,(0,0,0))

def _contourToTriangle(img: Cv2Image, contour: Cv2Contour) -> Triangle | None:
    imgperi = img.shape[0]*2 + img.shape[1]*2
    epsi = imgperi * 0.008
    approx = cv2.approxPolyDP(contour, epsi, True)
    if len(approx) != 3:
        return None

    triangle = approx.squeeze().tolist()

    hull = cv2.convexHull(contour)
    hullarea = cv2.contourArea(hull)
    cntarea = cv2.contourArea(contour)
    if cntarea < hullarea * 0.7:
        return None
    triarea = GeomCalc.polygonArea(triangle)
    if triarea < hullarea * 0.7:
        return None
    
    return triangle

def _getLongArrowData(img: Cv2Image, contour: Cv2Contour, direction: Point) -> ArrowData | None:
    points = contour.squeeze()
    maxy_point = max(points, key=lambda p: p[1])
    maxx_point = max(points, key=lambda p: p[0])
    miny_point = min(points, key=lambda p: p[1])
    minx_point = min(points, key=lambda p: p[0])

    maxydist = img.shape[0]-maxy_point[1]
    maxxdist = img.shape[1]-maxx_point[0]
    minydist = miny_point[1]
    minxdist = minx_point[0]

    pointdists = [(maxy_point,maxydist),
                  (maxx_point,maxxdist),
                  (miny_point,minydist),
                  (minx_point,minxdist)]
    closestpoint, closestdist = min(pointdists, key=lambda pointdist: pointdist[1])
    
    if direction == (0,1):
        if closestdist == minydist:
            if closestdist > img.shape[0] * 0.03:
                return None
            if miny_point[0]/img.shape[1] < 0.5:
                return ArrowData((-1,-1),direction,-1)
            else:
                return ArrowData((1,-1),direction,-1)
        if closestdist == minxdist and closestpoint[0] == minx_point[0] and closestpoint[1] == minx_point[1]:
            if closestdist > img.shape[1] * 0.03:
                return None
            return ArrowData((-1,0),direction, minx_point[1]/img.shape[0])
        if closestdist == maxxdist and closestpoint[0] == maxx_point[0] and closestpoint[1] == maxx_point[1]:
            if closestdist > img.shape[1] * 0.03:
                return None
            return ArrowData((1,0),direction, maxx_point[1]/img.shape[0])
    else:
        if closestdist == minxdist:
            if closestdist > img.shape[1] * 0.03:
                return None
            if miny_point[1]/img.shape[0] < 0.5:
                return ArrowData((-1,-1),direction,-1)
            else:
                return ArrowData((-1,1),direction,-1)
        if closestdist == minydist and closestpoint[0] == miny_point[0] and closestpoint[1] == miny_point[1]:
            if closestdist > img.shape[0] * 0.03:
                return None
            return ArrowData((0,-1),direction, miny_point[0]/img.shape[1])
        if closestdist == maxydist and closestpoint[0] == maxy_point[0] and closestpoint[1] == maxy_point[1]:
            if closestdist > img.shape[0] * 0.03:
                return None
            return ArrowData((0,1),direction, maxy_point[0]/img.shape[1])
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
    hull = cv2.convexHull(biggestcnt)
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