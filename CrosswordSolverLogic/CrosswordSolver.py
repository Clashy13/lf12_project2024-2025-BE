import os
from .DataSolve import Algorithm,answers_scrapper
from .DataExtraction import CrossWordDataExtraction
from .DataInsertion import AnswerInput
from lf12_crosswordReader_backend.models import CrosswordModel
from lf12_crosswordReader_backend import settings

from pathlib import Path
import cv2

def solve(imagepath):
    try:
        path = Path(imagepath)
        
        scannedimg, crossworddata = CrossWordDataExtraction.extractData(path)
        totalrects = []
        totalchars = []
        for i, cluster in enumerate(crossworddata.clustersdata):
            answerlines = answers_scrapper.CrosswordScraper().scrap(cluster.questionlines)
            chars = Algorithm.solve(len(cluster.answerrects),answerlines)
            totalrects.extend(cluster.answerrects)
            totalchars.extend(chars)
            for sol in crossworddata.solutioncells:
                if sol.clusterindexref == i:
                    totalrects.append(sol.rect)
                    totalchars.append(chars[sol.clustercellindexref])
        solvedimage = AnswerInput.putCharsToImage(scannedimg,totalrects,totalchars)
        orgid = path.stem
        solved_image_path = f"media/solved/{orgid}.jpg"
        cv2.imwrite(solved_image_path,solvedimage)
        obj = CrosswordModel.get(id = orgid) # type: ignore
        obj.solved_image = solved_image_path
        obj.save()
        
        return True
    except Exception as e:
        print(e)
        return e