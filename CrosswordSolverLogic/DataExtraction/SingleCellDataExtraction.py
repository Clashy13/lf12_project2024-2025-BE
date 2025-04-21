import numpy as np
from . import ImageProcessing as ImgProc
from . import ArrowDataExtraction as ArrowDataExtr
from ..Type import Cv2Image
from ..SingleCellData import CellContentData,DoubleQuestionData

import cv2
from PIL import Image
import re
import tesserocr

testdata = "./CrosswordSolverLogic/tessdata"
api = tesserocr.PyTessBaseAPI(path=testdata, lang='deu', psm=6) # type: ignore

def extractSingleCellData(img: Cv2Image) -> tuple[CellContentData,Cv2Image|None]:
    celldata = CellContentData()
    rightsizedimg = _resizeCellImage(img)
    arrowimg = ImgProc.preProcessArrowCell(rightsizedimg.copy())
    celldata.doublequestion = _extractDoubleQuestionData(rightsizedimg)
    if celldata.doublequestion:
        return celldata,None
    arrowcontours, arrowsdata = ArrowDataExtr.getArrows(rightsizedimg)
    celldata.arrows = arrowsdata
    if celldata.arrows:
        celldata.blank = True
    contours, _ = cv2.findContours(arrowimg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    filtered = []
    for cnt in contours:
        if ImgProc.contourNotEdge(cnt,img,4):
            filtered.append(cnt)
    arrowimg = ImgProc.fillContoursWhite(arrowimg, filtered)
    if arrowcontours:
        arrowimg = ImgProc.fillContours(arrowimg, arrowcontours,(0,0,0))
    
    cv2.imwrite("CrosswordSolverLogic/TmpCell/tmpCell.jpg",rightsizedimg)
    rightsizedimg = cv2.imread("CrosswordSolverLogic/TmpCell/tmpCell.jpg")
    
    textimg = ImgProc.preProcessTextCell(rightsizedimg.copy(),arrowcontours)

    bordered = ImgProc.drawBorder(textimg.copy(),(0,0,0),10)
    if _imageEmpty(bordered) or _imageEmpty(cv2.threshold(bordered,10,255,cv2.THRESH_BINARY)[1]):
        celldata.blank = True
        return celldata,None
    
    return celldata,textimg

def extractQuestionData(img: Cv2Image) -> str:
    api.SetVariable('tessedit_char_whitelist', 'abcdefghijklmnopqrstuvwxyzäöüABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÜ0123456789,;.:-—()ß?“„ ')
    text = _extractText(img)
    return text

def extractNumberData(img: Cv2Image) -> int | None:
    api.SetVariable('tessedit_char_whitelist', '1234567890,;.:-—+*')
    api.SetImage(Image.fromarray(255-np.hstack((img,img))))
    text: str = api.GetUTF8Text()
    text = re.sub("[^0-9]", "", text)
    text = text[:int(len(text)/2)]
    if len(text) != 0:
        return int(text)
    return None

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

def _extractDoubleQuestionData(img: Cv2Image) -> DoubleQuestionData | None:
    textimages = ImgProc.preProcessDoubleQuestionCell(img)
    if textimages is None:
        return None
    position = textimages[0].shape[0]/(textimages[0].shape[0]+textimages[1].shape[0])
    textimg1 = ImgProc.preProcessTextCell(textimages[0],[])
    textimg2 = ImgProc.preProcessTextCell(textimages[1],[])
    text1 = extractQuestionData(textimg1)
    text2 = extractQuestionData(textimg2)
    return DoubleQuestionData(text1,text2,position)

def _imageEmpty(img:Cv2Image) -> bool:
    return cv2.countNonZero(img) <= 100

def _resizeCellImage(img: Cv2Image) -> Cv2Image:
    newheight = 166
    oldheight = img.shape[0]
    factor = newheight / oldheight
    return cv2.resize(img, (0, 0), fx = factor, fy = factor)
