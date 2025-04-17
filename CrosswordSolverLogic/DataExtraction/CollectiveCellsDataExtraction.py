from CrosswordSolverLogic.SingleCellData import SingleQuestionData
from ..Utility import ImageWarping as ImgWp
from . import SingleCellDataExtraction as SCellDataExtr
from . import CellIndexing as CellIndx
from ..SingleCellData import CellRect,CellData,CellIndex,ArrowData,SolutionCellData
from ..CollectiveCellData import QuestionLine,ClusterData,CrossWordData
from ..Type import Cv2Image

def extractCellsData(img: Cv2Image, cellrects: list[CellRect]) -> CrossWordData:
    indvcellsdata = _extractIndividualCellsData(img,cellrects)
    solutioncells = _extractSolutionCells(indvcellsdata)
    maxcluster = max(cell.index.cluster for cell in indvcellsdata)
    cellclusters: list[list[CellData]] = []
    for i in range(maxcluster+1):
        cellclusters.append([])

    for cell in indvcellsdata:
        cellclusters[cell.index.cluster].append(cell)

    cellclusters = [cluster for cluster in cellclusters if cluster]

    clustersdata: list[ClusterData] = []
    for i, cluster in enumerate(cellclusters):
        blankcells = [cell for cell in cluster if cell.content.blank]
        if solutioncells:
            _setSolutionReferences(solutioncells,i,blankcells)

        arrowcells = [cell for cell in blankcells if cell.content.arrows]
        questioncells = [cell for cell in cluster if cell.content.doublequestion or cell.content.singlequestion]

        questionlines: list[QuestionLine] = []
        for arrowcell in arrowcells:
            for arrow in arrowcell.content.arrows:
                questionlines.append(_getQuestionCellLine(arrow,arrowcell.index,blankcells,questioncells))
        
        blankrects = [cell.rect for cell in blankcells]
        clustersdata.append(ClusterData(questionlines,blankrects))
    
    return CrossWordData(clustersdata,solutioncells)

def _extractSolutionCells(indvcellsdata: list[CellData]) -> list[SolutionCellData]:
    numbercells = [cell for cell in indvcellsdata if cell.content.number]
    if not numbercells:
        return []
    maxnum = int(len(numbercells)/2)

    if len(numbercells) % 2 != 0:
        raise Exception("Error while extracting collective cell data: count of cells with a number doesn't match")
    for i in range(1,maxnum+1):
        count = sum(cell.content.number == i for cell in numbercells)
        if count == 0:
            raise Exception(f"Error while extracting collective cell data: no cell with number \'{i}\' found")
        if count == 1:
            raise Exception(f"Error while extracting collective cell data: only one cell with number \'{i}\' found")
        elif count > 2:
            raise Exception(f"Error while extracting collective cell data: too many cells with number \'{i}\' found")


    solutioncells = []
    onecells = [cell for cell in numbercells if cell.content.number == 1]
    for cell in onecells:
        idxpath = [CellIndex(cell.index.cluster,cell.index.row,cell.index.column+i) for i in range(maxnum)]
        cellspath: list[CellData] = []
        complete = True
        for i in range(maxnum):
            numcells = [cell for cell in numbercells if cell.index == idxpath[i]]
            if numcells and numcells[0].content.number == i+1:
                cellspath.append(numcells[0])
            else:
                complete = False
                break
        if complete:
            for cell in cellspath:
                solutioncell = SolutionCellData()
                solutioncell.setRect(cell.rect)
                solutioncells.append(solutioncell)
            for cell in cellspath:
                indvcellsdata.remove(cell)
            return solutioncells
        
    raise Exception("Error while extracting collective cell data: solution cell row not found")

def _setSolutionReferences(solutioncells: list[SolutionCellData], clusterindex: int, blankcells: list[CellData]):
    for i,cell in enumerate(blankcells):
        if cell.content.number:
            try:
                solutioncells[cell.content.number-1].setClusterIndexReference(clusterindex)
                solutioncells[cell.content.number-1].setClusterCellIndexReference(i)
            except:
                raise Exception(f"Error while extracting collective cell data: number \'{cell.content.number-1}\' out of bound of solution cells")
    

def _getQuestionCellLine(arrow: ArrowData, index: CellIndex, blankcells: list[CellData], questioncells: list[CellData]) -> QuestionLine:
    questionindex = CellIndex(index.cluster,index.row+arrow.origin[1],index.column+arrow.origin[0])
    questioncell = None
    for cell in questioncells:
        if cell.index == questionindex:
            questioncell = cell
            break
    if questioncell is None:
        raise Exception("Error while extracting collective cell data: no question cell for arrow found")

    question = ""
    if questioncell.content.doublequestion:
        if arrow.direction == (0,1):
            question = questioncell.content.doublequestion.question2
        else:
            if arrow.position < questioncell.content.doublequestion.lineposition:
                question = questioncell.content.doublequestion.question1
            else:
                question = questioncell.content.doublequestion.question2
    elif questioncell.content.singlequestion is not None:
        question = questioncell.content.singlequestion.question

    currentcellindex = index
    answerindexes: list[int] = []
    while True:
        indexes = [i for i,cell in enumerate(blankcells) if cell.index == currentcellindex]
        if indexes:
            currentblankindex = indexes[0]
            answerindexes.append(currentblankindex)
            currentcellindex = CellIndex(currentcellindex.cluster,currentcellindex.row+arrow.direction[1],currentcellindex.column+arrow.direction[0])
        else:
            break
    return QuestionLine(question,answerindexes)

def _extractIndividualCellsData(img: Cv2Image,cellrects: list[CellRect]) -> list[CellData]:
    indexes = CellIndx.getindexedCells(cellrects)

    indvcellsdata: list[CellData] = []
    textimages = []
    for i,rect in enumerate(cellrects):
        index = indexes[i]

        cellimg = ImgWp.warpRect(img.copy(),rect)
        content, textimg = SCellDataExtr.extractSingleCellData(cellimg)

        textimages.append(textimg)

        indvcellsdata.append(CellData(rect,index,content))

    questionidxs = []
    for i,celldata in enumerate(indvcellsdata):
        idx = indexes[i]
        for arrow in celldata.content.arrows:
           questionidxs.append(CellIndex(idx.cluster,idx.row+arrow.origin[1],idx.column+arrow.origin[0]))
    
    for i, textimg in enumerate(textimages):
        if textimg is None:
            continue
        if indexes[i] in questionidxs:
            text = SCellDataExtr.extractQuestionData(textimg)
            indvcellsdata[i].content.singlequestion = SingleQuestionData(text)
        else:
            num = SCellDataExtr.extractNumberData(textimg)
            if num is not None:
                indvcellsdata[i].content.number = num
            indvcellsdata[i].content.blank = True

    return indvcellsdata

def _getNextCells(index: CellIndex ,number: int, numbercells: dict, maxnumber: int) -> list:
    nextindex = CellIndex(index.cluster, index.row,index.column+1)
    nextnum = number+1
    if nextnum > maxnumber:
        return []
    solutioncells = []
    if nextindex in numbercells and numbercells[nextindex] == nextnum:
        both = [idx for idx, num in numbercells.items() if num == nextnum]
        otherindex = both[0] if both[0] != nextindex else both[1]
        solutioncells = [(nextindex,otherindex)] + _getNextCells(nextindex, nextnum, numbercells, maxnumber)
    return solutioncells