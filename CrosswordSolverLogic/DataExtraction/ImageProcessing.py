from ..Type import Cv2Image, Cv2Contour, Color

import cv2
import numpy as np

sr = cv2.dnn_superres.DnnSuperResImpl_create() # type: ignore
sr.readModel("CrosswordSolverLogic/TensorFlow/ESPCN_x2.pb")
sr.setModel("espcn",2)

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

def preProcessTextCell(img: Cv2Image) -> Cv2Image:
    sigma = 2
    strength = 3
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (0,0), sigmaX=15, sigmaY=15)
    divide = cv2.divide(gray, blur, scale=255)
    blurred = cv2.GaussianBlur(divide, (0, 0), sigma)
    sharpened = cv2.addWeighted(divide, 1.0 + strength, blurred, -strength, 0)
    bit = cv2.bitwise_not(sharpened)
    unbordered = _drawborderImage(bit,(0,0,0))

    textimg = unbordered

    contours, _ = cv2.findContours(textimg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    nonfilteredcontours = []
    for cnt in contours:
        mask = np.ones_like(textimg) * 0
        cv2.drawContours(mask, [cnt], -1, (255, 255, 255),-1, cv2.LINE_AA)
        image_masked = cv2.bitwise_and(textimg, mask)
        maxv = np.amax(image_masked)
        if maxv <= 170:
            nonfilteredcontours.append(cnt)

    filled = fillContours(textimg,nonfilteredcontours,(0,0,0))

    brightness = 1
    contrast = 3
    brighter = cv2.addWeighted(filled, contrast, np.zeros(filled.shape, filled.dtype), 0, brightness) 
    return brighter

def preProcessArrowCell(img: Cv2Image) -> Cv2Image:
    c = 10000/(img.shape[0]+img.shape[1])
    grey = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(grey, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                      cv2.THRESH_BINARY_INV, 101, c)
    unbordered = _drawborderImage(thresh,(0,0,0))

    contours, _ = cv2.findContours(unbordered, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    imgarea = img.shape[0]*img.shape[1]
    filtered = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < imgarea * 0.005:
            filtered.append(cnt)
    filled = fillContours(unbordered,filtered,(0,0,0))

    return filled

def preProcessArrowHeadCell(img: Cv2Image) -> Cv2Image:
    c = 5200/(img.shape[0]+img.shape[1])
    grey = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(grey, (0, 0), 2)
    sharpened = cv2.addWeighted(grey, 1.0 + 3, blurred, -3, 0)
    blur = cv2.GaussianBlur(sharpened, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                      cv2.THRESH_BINARY_INV, 91, c)
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    for i,cnt in enumerate(contours):
         if hierarchy[0][i][3] != -1:
              thresh = fillContours(thresh,[cnt],(255,255,255))
    f = 0.025
    k = int(np.rint(f * (img.shape[0]+img.shape[1])))
    kernel = cv2.getStructuringElement( cv2.MORPH_RECT, (k,k), (-1,-1) )
    erode = cv2.erode(thresh,kernel)
    unbordered = _drawborderImage(erode,(0,0,0))
    return unbordered

def _drawborderImage(img: Cv2Image,color: Color) -> Cv2Image:
    width = int(img.shape[1] * 0.04)
    height = int(img.shape[0] * 0.04)
    cv2.line(img,(0,0),(0,img.shape[0]-1),color,width)
    cv2.line(img,(0,img.shape[0]-1),(img.shape[1]-1,img.shape[0]-1),color,height)
    cv2.line(img,(img.shape[1]-1,img.shape[0]-1),(img.shape[1]-1,0),color,width)
    cv2.line(img,(img.shape[1]-1,0),(0,0),color,height)
    return img

def fillContours(img: Cv2Image, contours: list[Cv2Contour], color: Color) -> Cv2Image:
    for contour in contours:
        if len(contour) >= 3:
            cv2.fillPoly(img, pts=[contour.squeeze()], color=color)
    return img

def fillContoursBlack(img: Cv2Image, contours: list[Cv2Contour]) -> Cv2Image:
    mask = np.ones_like(img) * 255
    cv2.drawContours(mask, contours, -1, (0, 0, 0),-1, cv2.LINE_AA)
    return mask

def fillContoursWhite(img: Cv2Image, contours: list[Cv2Contour]) -> Cv2Image:
	mask = np.ones_like(img) * 0
	cv2.drawContours(mask, contours, -1, (255, 255, 255),-1, cv2.LINE_AA)
	return mask

def fillBackgroundBlack(img: Cv2Image, contours: list[Cv2Contour]) -> Cv2Image:
    mask = np.ones_like(img) * 255
    cv2.drawContours(mask, contours, -1, (0, 0, 0),-1, cv2.LINE_AA)
    image_masked = cv2.bitwise_and(img, (255- mask))
    bckgnd_masked = cv2.bitwise_and(0,  mask) # type: ignore
    return cv2.add(image_masked, bckgnd_masked)

def upscaleImage(img: Cv2Image) -> Cv2Image:
    return sr.upsample(img)

def contoursIntersect(original_image: Cv2Image, contour1: Cv2Contour, contour2: Cv2Contour) -> bool:
    blank = np.zeros(original_image.shape[:2])
    image1 = cv2.fillPoly(blank.copy(), [contour1], 255) # type: ignore
    image2 = cv2.fillPoly(blank.copy(), [contour2], 255) # type: ignore
    intersection = np.logical_and(image1, image2)
    return intersection.any()
