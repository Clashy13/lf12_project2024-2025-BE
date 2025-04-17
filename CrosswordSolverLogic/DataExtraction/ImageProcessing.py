from CrosswordSolverLogic.SingleCellData import CellRect
from ..Type import Cv2Image, Cv2Contour, Color
from ..Utility import ImageWarping as ImgWp

import math
import cv2
import numpy as np

def prePreProcessGrid(img):
    grey = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(grey, (11, 11), 0)
    thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                      cv2.THRESH_BINARY_INV, 3, 2)
    kernel = np.ones((3,3),np.uint8)
    dilation = cv2.dilate(thresh,kernel,iterations = 2)
    return dilation

def preProcessGrid(img):
    grey = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(grey, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                      cv2.THRESH_BINARY_INV, 51, 11)
    return thresh

def preProcessTextCell(img: Cv2Image, arrowcontours: list[Cv2Contour]) -> Cv2Image:
    grey = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(grey, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                      cv2.THRESH_BINARY_INV, 11, 7)
    
    kernel = np.ones((3,3),np.uint8)
    dilate = cv2.dilate(thresh,kernel,iterations = 1)

    filtered = []
    contours, _ = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        if _contourOnEdge(cnt,dilate) and not contourNotEdge(cnt,dilate,10):
            continue
        if cv2.contourArea(cnt) > cv2.arcLength(cnt, True):
            filtered.append(cnt)
    mask1 = fillContoursWhite(dilate,filtered)
    contours1, _ = cv2.findContours(mask1, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    sigma = 2
    strength = 3
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (0,0), sigmaX=15, sigmaY=15)
    divide = cv2.divide(gray, blur, scale=255)
    blurred = cv2.GaussianBlur(divide, (0, 0), sigma)
    sharpened = cv2.addWeighted(divide, 1.0 + strength, blurred, -strength, 0)
    bit = cv2.bitwise_not(sharpened)
    textimg = fillContours(bit,arrowcontours,(0,0,0))

    brightness = 1
    contrast = 3
    textimg = cv2.addWeighted(textimg, contrast, np.zeros(textimg.shape, textimg.dtype), 0, brightness)

    textimg = cv2.bitwise_and(textimg, mask1)
    contours, _ = cv2.findContours(cv2.threshold(textimg,10,255,cv2.THRESH_BINARY)[1], cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    filteredcontours = []
    for cnt in contours:
        if _contourOnEdge(cnt,textimg):
            if not contourNotEdge(cnt,textimg,10):
                filteredcontours.append(cnt)
    textimg = fillContours(textimg,filteredcontours,(0,0,0))

    filteredcontours = []
    for cnt in contours1:
        cntmask = textimg* 0
        cv2.drawContours(cntmask, [cnt], -1, (255, 255, 255),-1, cv2.LINE_AA)
        image_masked = cv2.bitwise_and(textimg, cntmask)
        if cv2.countNonZero(image_masked) == 0:
            continue

        non_zero_pixels = image_masked[image_masked > 1]
        if non_zero_pixels.size == 0:
            continue
        meanv = non_zero_pixels.mean()
        maxv = non_zero_pixels.max()
        if meanv <= 170 or maxv <= 200:
            continue

        filteredcontours.append(cnt)

    mask = np.ones_like(textimg) * 0
    cv2.drawContours(mask, filteredcontours, -1, (255, 255, 255),-1, cv2.LINE_AA)
    filled = cv2.bitwise_and(textimg, mask)
    
    return cv2.bitwise_and(filled, mask1)

def preProcessDoubleQuestionCell(img: Cv2Image) -> tuple[Cv2Image,Cv2Image] | None:
    grey = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(grey, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                      cv2.THRESH_BINARY_INV, 15, 31)
    border = drawBorder(thresh,(255,255,255),1)
    contours, hierarchy = cv2.findContours(border, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    contours = list(contours)

    imgarea = img.shape[0]*img.shape[1]
    bigidx = -1
    for i,cnt in enumerate(contours):
        if cv2.contourArea(cnt) > imgarea * 0.98:
            bigidx = i
            break
    if bigidx == -1:
        return None
    cntboxes = []
    for cnt,hier in zip(contours,hierarchy[0]):
        if hier[3] == bigidx:
            cntboxes.append(cnt)

    if len(cntboxes) < 2:
        return None

    for i,cnt in enumerate(cntboxes):
        cntboxes[i] = cv2.convexHull(cnt)

    removedidxs = []
    for i in range(len(cntboxes)):
        area1 = cv2.contourArea(cntboxes[i])
        (x, y), _, _ = cv2.minAreaRect(cntboxes[i])
        for j in range(len(cntboxes)):
            if i != j:
                area2 = cv2.contourArea(cntboxes[j])
                x2, y2, w2, h2 = cv2.boundingRect(cntboxes[j])
                if x > x2 and x < x2+w2 and y > y2 and y < y2+h2 and area1 < area2:
                    removedidxs.append(i)
    
    cntboxes = [cnt for i,cnt in enumerate(cntboxes) if i not in removedidxs]
    if len(cntboxes) != 2:
        return None
    
    rects = [CellRect(CellRect.pointsToRect(cnt.squeeze().tolist())) for cnt in cntboxes]
    rects = sorted(rects, key=lambda r : r.center()[1])
    
    return (ImgWp.warpRect(img,rects[0]),
            ImgWp.warpRect(img,rects[1]))

def preProcessArrowCell(img: Cv2Image) -> Cv2Image:
    grey = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(grey, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                      cv2.THRESH_BINARY_INV, 101, 11)
    
    h,w = img.shape[:2]
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    hascircle = False
    filtered = []
    for cnt,hier in zip(contours,hierarchy[0]):
        if hier[3] != -1:
            continue
        if cv2.contourArea(cnt) <= cv2.arcLength(cnt, True):
            continue
        _,_,cw,ch = cv2.boundingRect(cnt)
        if cw > w * 0.75 and ch > h * 0.75:
            hascircle = True
            filtered.append(cnt)
            continue
        if hier[2] != -1:
            continue
        if _contourOnEdge(cnt,img):
            filtered.append(cnt)

    mask1 = fillContoursWhite(thresh,filtered)

    if not hascircle:
        return mask1

    grey = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(grey, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                      cv2.THRESH_BINARY_INV, 31, 31)
    bit = cv2.bitwise_and(mask1,thresh)

    contours, _ = cv2.findContours(bit, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    filtered = []
    for cnt in contours:
        if not any(p[0][0] < img.shape[1]/2 or p[0][1] < img.shape[0]/2 for p in cnt):
            filtered.append(cnt)
    mask2 = fillContoursWhite(bit,filtered)
    kernel = np.ones((3,3),np.uint8)
    mask2 = cv2.dilate(mask2,kernel,iterations = 4)

    sub = cv2.subtract(mask1,mask2)
    return cv2.dilate(sub,kernel,iterations = 2)

def preProcessArrowHeadCell(img: Cv2Image) -> Cv2Image:
    grey = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(grey, (5, 5), 0)
    processed = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                      cv2.THRESH_BINARY_INV, 101, 11)
    count = cv2.countNonZero(processed)
    kernel = np.ones((7,7),np.uint8)
    gradient = cv2.morphologyEx(processed, cv2.MORPH_GRADIENT, kernel)
    kernel = np.ones((3,3),np.uint8)
    arrowimg = cv2.erode(255-gradient,kernel)

    contours, hierarchy = cv2.findContours(arrowimg, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    cnts = [cnt for cnt,hier in zip(contours,hierarchy[0]) if hier[2] == -1]
    arrowmax = 0.05 * (arrowimg.shape[0]*arrowimg.shape[1])
    arrowmin =  0.002 * (arrowimg.shape[0]*arrowimg.shape[1])
    filtered = []
    for cnt in cnts:
        area = cv2.contourArea(cnt)
        if area > arrowmax or area < arrowmin:
            continue
        mask = processed.copy()
        cv2.drawContours(mask, [cnt], -1, (255, 255, 255),-1, cv2.LINE_AA) # type: ignore
        if cv2.countNonZero(mask) == count:
            filtered.append(cnt)
    
    return fillContoursWhite(arrowimg,filtered)

def _contourOnEdge(contour: Cv2Contour, img: Cv2Image) -> bool:
    h,w = img.shape[:2]
    for p in contour:
        if p[0][0] == 0 or p[0][0] == w-1 or p[0][1] == 0 or p[0][1] == h-1:
            return True
    return False

def contourNotEdge(contour: Cv2Contour, img: Cv2Image, borderwidth: int) -> bool:
    h,w = img.shape[:2]
    for pt in contour:
        p = pt[0]
        if p[0] > borderwidth and p[1] > borderwidth and p[0] < w-borderwidth-1 and p[1] < h-borderwidth-1:
            return True
    return False

def drawBorder(img: Cv2Image, color: Color, thickness: int) -> Cv2Image:
    cv2.line(img,(0,0),(0,img.shape[0]-1),color,thickness)
    cv2.line(img,(0,img.shape[0]-1),(img.shape[1]-1,img.shape[0]-1),color,thickness)
    cv2.line(img,(img.shape[1]-1,img.shape[0]-1),(img.shape[1]-1,0),color,thickness)
    cv2.line(img,(img.shape[1]-1,0),(0,0),color,thickness)
    return img

def fillContours(img: Cv2Image, contours: list[Cv2Contour], color: Color) -> Cv2Image:
    for contour in contours:
        if len(contour) >= 3:
            cv2.fillPoly(img, pts=[contour.squeeze()], color=color)
    return img

def fillContoursWhite(img: Cv2Image, contours: list[Cv2Contour]) -> Cv2Image:
	mask = np.ones_like(img) * 0
	cv2.drawContours(mask, contours, -1, (255, 255, 255),-1, cv2.LINE_AA) # type: ignore
	return cv2.threshold(mask,127,255,cv2.THRESH_BINARY)[1]

def fillBackgroundBlack(img: Cv2Image, contours: list[Cv2Contour]) -> Cv2Image:
    mask = np.ones_like(img) * 255
    cv2.drawContours(mask, contours, -1, (0, 0, 0),-1, cv2.LINE_AA) # type: ignore
    image_masked = cv2.bitwise_and(img, (255- mask))
    bckgnd_masked = cv2.bitwise_and(0,  mask) # type: ignore
    return cv2.add(image_masked, bckgnd_masked)
