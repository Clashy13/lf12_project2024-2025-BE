from ..Utility import ImageWarping as ImgWp
from ..Type import Cv2Image
from ..SingleCellData import CellRect

import cv2
import numpy as np

def putCharsToImage(img: Cv2Image, rects: list[CellRect], chars: list[str]) -> Cv2Image:
    mask = np.ones_like(img) * 0
    blue = mask.copy()
    blue[:] = (78,20,15)
    for i, rect in enumerate(rects):
        mask = _putCharToImage(mask,rect, chars[i])
    foreground = cv2.bitwise_and(mask,blue)
    background = cv2.bitwise_and(255-mask,img)
    return cv2.add(foreground, background)

def _putCharToImage(img: Cv2Image, rect: CellRect, char: str):
    warpedimg, matrix = ImgWp.warpRectWithMatrix(img, rect)
    fontScale = min(warpedimg.shape[1],warpedimg.shape[0])/27
    thickness = int(fontScale*1.5)
    textsize = cv2.getTextSize(char, cv2.FONT_HERSHEY_DUPLEX, fontScale, thickness)[0]
    textX = int((warpedimg.shape[1] - textsize[0]) / 2)
    textY = int((warpedimg.shape[0] + textsize[1]) / 2)

    mask = np.ones_like(warpedimg) * 0
    cv2.putText(mask,char,(textX,textY),cv2.FONT_HERSHEY_DUPLEX,fontScale,(255,255,255),thickness)
    bigmask = cv2.warpPerspective(mask,np.linalg.pinv(matrix),(img.shape[1], img.shape[0]),flags=cv2.INTER_LINEAR)
    return cv2.add(bigmask, img)
