from . import ImageProcessing as ImgProc
from . import ArrowDataExtraction as ArrowDataExtr
from ..Type import Cv2Image, Cv2Contour
from ..SingleCellData import CellContentData,DoubleQuestionData,SingleQuestionData

import cv2
from PIL import Image
import numpy as np
import re
import tesserocr

testdata = "./CrosswordSolverLogic/tessdata"
api = tesserocr.PyTessBaseAPI(path=testdata, lang='deu', psm=6) # type: ignore
api.SetVariable('tessedit_char_whitelist', 'abcdefghijklmnopqrstuvwxyzäöüABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÜ0123456789,;.:-—()ß“„ ')

def extractSingleCellData(img: Cv2Image) -> CellContentData:
    celldata = CellContentData()

    img = ImgProc.upscaleImage(img)

    arrowimg = ImgProc.preProcessArrowCell(img.copy())

    celldata.doublequestion = _extractDoubleQuestionData(img,arrowimg)
    if celldata.doublequestion:
        return celldata
    
    arrowcontours, arrowsdata = ArrowDataExtr.getArrows(img)
    if arrowcontours:
        arrowimg = ImgProc.fillContours(arrowimg, arrowcontours,(0,0,0))
    celldata.arrows = arrowsdata
    if celldata.arrows:
        celldata.blank = True
        
    if _imageEmpty(arrowimg):
        celldata.blank = True
        return celldata
    
    cv2.imwrite("CrosswordSolverLogic/TmpCell/tmpCell.jpg",img)
    img = cv2.imread("CrosswordSolverLogic/TmpCell/tmpCell.jpg")

    textimg = ImgProc.preProcessTextCell(img.copy())

    if arrowcontours:
        mask = ImgProc.fillContoursWhite(arrowimg,arrowcontours)
        kernel = np.ones((3,3),np.uint8)
        dilation = cv2.dilate(mask,kernel,iterations = 1)
        biggerarrowcontours,_ = cv2.findContours(dilation, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        textimg = ImgProc.fillContours(textimg, list(biggerarrowcontours),(0,0,0))

    newheight = 166
    oldheight = textimg.shape[0]
    factor = newheight / oldheight
    rightsizedimg = cv2.resize(textimg, (0, 0), fx = factor, fy = factor)
    
    text = _extractText(rightsizedimg)

    dcount = 0
    lcount = 0
    for c in text:
        if c.isdigit():
            dcount += 1
        elif c.isalpha():
            lcount += 1
    
    if dcount == 0 and lcount == 0:
        pass
    elif dcount >= lcount:
        number = int(''.join(filter(lambda x: x.isdigit(), text)))
        celldata.number = number
    elif lcount > 0 and not celldata.arrows:
        celldata.singlequestion = SingleQuestionData(text)

    if celldata.singlequestion is None:
        celldata.blank = True
            
    return celldata

def _extractText(img: Cv2Image) -> str:
    api.SetImage(Image.fromarray(255-img))
    text: str = api.GetUTF8Text()
    text = text.replace("—", "-")
    text = text.replace("\n", " ")
    text = re.sub(" +", " ", text)
    text = re.sub(" *- *(?=[A-Z])", "-", text)
    text = re.sub(" *- *(?=[a-z])", "", text)
    text = re.sub("-+", "-", text)
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2',text)
    text = re.sub(" (\\+|\\-)", " ", text)
    text = re.sub(" \\.(?!\\.)", " ", text)
    text = text.strip()
    return text

def _extractDoubleQuestionData(img: Cv2Image, arrowimg: Cv2Image) -> DoubleQuestionData | None:
    contours, _ = cv2.findContours(arrowimg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    linecontour, position = _findDoubleQuestionLine(arrowimg.copy(),list(contours))

    if position and linecontour:
        textimg = ImgProc.preProcessTextCell(img.copy())
        textimg = ImgProc.fillContours(textimg, [linecontour],(0,0,0))
        pos = int(position * textimg.shape[0])
        topimg = textimg[:pos, :]
        bottomimg = textimg[pos:, :]
        
        text1 = _extractText(topimg)
        text2 = _extractText(bottomimg)
        return DoubleQuestionData(text1,text2,position)
    return None


def _findDoubleQuestionLine(img: Cv2Image, contours: list[Cv2Contour]) -> tuple[Cv2Contour | None,float | None]:
    hullfactor = 0.4
    widthfactor = 0.06
    heightfactor = 0.05
    for contour in contours:
        hull = cv2.convexHull(contour)
        area1 = cv2.contourArea(contour)
        area2 = cv2.contourArea(hull)
        x, y, w, h = cv2.boundingRect(hull)
        if (area1 <= area2 * (1+hullfactor) and 
            area1 >= area2 * (1-hullfactor) and
            w >= img.shape[1] * (1-widthfactor) and
            h <= img.shape[0] *  heightfactor):
            position = (y + int(h/2)) / img.shape[0]
            return hull, position
    return None, None

def _imageEmpty(img:Cv2Image) -> bool:
    return cv2.countNonZero(img) <= 20
