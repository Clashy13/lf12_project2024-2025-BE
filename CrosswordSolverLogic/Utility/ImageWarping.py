from ..SingleCellData import CellRect
from ..Type import Cv2Image, Cv2Matrix

import numpy as np
import cv2

def warpRect(img: Cv2Image, rect: CellRect) -> Cv2Image:
    a,b,c,d = rect

    width_ad = np.sqrt(((a[0] - d[0]) ** 2) + ((a[1] - d[1]) ** 2))
    width_bc = np.sqrt(((b[0] - c[0]) ** 2) + ((b[1] - c[1]) ** 2))
    maxwidth = max(int(width_ad), int(width_bc))
    
    height_ab = np.sqrt(((a[0] - b[0]) ** 2) + ((a[1] - b[1]) ** 2))
    height_cd = np.sqrt(((c[0] - d[0]) ** 2) + ((c[1] - d[1]) ** 2))
    maxheight = max(int(height_ab), int(height_cd))
    
    input_pts = np.float32([a, b, c, d]) # type: ignore
    output_pts = np.float32([[0, 0], # type: ignore
                            [0, maxheight - 1],
                            [maxwidth - 1, maxheight - 1],
                            [maxwidth - 1, 0]])
    
    m = cv2.getPerspectiveTransform(input_pts,output_pts) # type: ignore
    
    out = cv2.warpPerspective(img,m,(maxwidth, maxheight),flags=cv2.INTER_LINEAR)

    return out

def warpRectWithMatrix(img: Cv2Image, rect: CellRect) -> tuple[Cv2Image, Cv2Matrix]:
    a,b,c,d = rect

    width_ad = np.sqrt(((a[0] - d[0]) ** 2) + ((a[1] - d[1]) ** 2))
    width_bc = np.sqrt(((b[0] - c[0]) ** 2) + ((b[1] - c[1]) ** 2))
    maxwidth = max(int(width_ad), int(width_bc))
    
    height_ab = np.sqrt(((a[0] - b[0]) ** 2) + ((a[1] - b[1]) ** 2))
    height_cd = np.sqrt(((c[0] - d[0]) ** 2) + ((c[1] - d[1]) ** 2))
    maxheight = max(int(height_ab), int(height_cd))
    
    input_pts = np.float32([a, b, c, d]) # type: ignore
    output_pts = np.float32([[0, 0], # type: ignore
                            [0, maxheight - 1],
                            [maxwidth - 1, maxheight - 1],
                            [maxwidth - 1, 0]])
    
    matrix = cv2.getPerspectiveTransform(input_pts,output_pts) # type: ignore
    
    out = cv2.warpPerspective(img,matrix,(maxwidth, maxheight),flags=cv2.INTER_LINEAR)

    return out,matrix