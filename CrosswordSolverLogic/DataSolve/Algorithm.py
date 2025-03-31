from . import  AnswerLine

import time

starttime = 0.

def countAnswerConnections(answers: list[AnswerLine], idx: int) -> int:
    count = 0
    for cellidx in answers[idx].cellindexes:
        for i,answer in enumerate(answers):
            if idx != i and cellidx in answer.cellindexes:
                count += 1
                break
    return count

def wordFits(word: str, cellindexes: list[int], solution: list[str]):
    for i in range(len(cellindexes)):
        if solution[cellindexes[i]] != "" and solution[cellindexes[i]] != word[i]:
            return False
    return True

def createSolutionWithWord(word: str, cellindexes: list[int], solution: list[str]) -> list[str]:
    newsolution = solution.copy()
    for i in range(len(cellindexes)):
        newsolution[cellindexes[i]] = word[i]
    return newsolution

def filterConnectedAnswerIndexes(answers: list[AnswerLine], filledansweridxs: list[int], solution: list[str]) -> list:
    filtered = []
    for i,answer in enumerate(answers):
        if i in filledansweridxs:
            continue
        connected = False
        for othercellidx in answer.cellindexes:
            if solution[othercellidx] != "":
                connected = True
                break
        if connected:
            filtered.append(i)
    return filtered

def finalSolution(answerlinecount: int, solutions: list[list[str]]) -> bool:
    global starttime
    if time.time() - starttime >= answerlinecount/10:
        return True
    for s in solutions:
        if s.count("") == 0:
            return True
    return False

def getSolutions(answeridx: int, answers: list[AnswerLine], filledansweridxs: list[int], solution: list[str]) -> tuple[list[list[str]], bool]:
    totalsolutions = []
    answer = answers[answeridx]
    cellidxs = answer.cellindexes
    totalfinal = False
    for word in answer.answers:
        if not wordFits(word,cellidxs,solution):
            continue

        newsolution = createSolutionWithWord(word,cellidxs,solution)
        newfilledansweridxs = filledansweridxs + [answeridx]

        connectedanswersidxs = filterConnectedAnswerIndexes(answers,newfilledansweridxs,newsolution)
        # sortedansweridxs = sorted(connectedanswersidxs, key= lambda idx : len(answers[idx].answers))

        solutions = []
        for i in connectedanswersidxs:
            localsolutions, final = getSolutions(i,answers,newfilledansweridxs,newsolution)
            solutions.extend(localsolutions)
            if final or finalSolution(len(answers),localsolutions):
                totalfinal = True
                break

        if not solutions:
            solutions = [newsolution]
        
        totalsolutions.extend(solutions)

        if totalfinal:
            break
    return totalsolutions, totalfinal

def solveAnswers(cellcount: int, answers: list[AnswerLine]) -> list[str]:
    answers = sorted(answers, key= lambda answer: len(answer.answers))
    global starttime
    starttime = time.time()
    emptysolution = ["" for i in range(cellcount)]
    solutions: list[list] = []
    for i in range(len(answers)):
        localsolution, final = getSolutions(i,answers,[],emptysolution.copy())
        if final:
            solutions = localsolution
            break
        solutions.extend(localsolution)

    bestsolution = min(solutions, key= lambda solution: solution.count(""))
    return bestsolution

def sortAnswers(answerlines: list[AnswerLine]):
    for i, answerline in enumerate(answerlines):
        letterslist = []
        for cellidx in answerline.cellindexes:
            otheranswerline = next((a for j,a in enumerate(answerlines) if cellidx in a.cellindexes and i != j),None)
            if otheranswerline is not None:
                letteridx = otheranswerline.cellindexes.index(cellidx)
                letters = [a[letteridx] for a in otheranswerline.answers]
                letterslist.append(letters)
            else:
                letterslist.append([])
        counts = []
        newanswers = []
        for answer in answerline.answers:
            countfits = 0
            for letter, crossletters in zip(answer,letterslist):
                if not crossletters:
                    countfits += 1
                elif letter in crossletters:
                    countfits += 1
            if countfits > 0:
                counts.append(countfits)
                newanswers.append(answer)

        newanswers = [x for _, x in sorted(zip(counts, newanswers),reverse=True)]
        answerlines[i].answers = newanswers

def sortAnswerLines(answerlines: list[AnswerLine]):
    saveanswers = []
    notsaveanswers = []
    for answerline in answerlines:
        if answerline.similarity == 1.0:
            saveanswers.append(answerline)
        else:
            notsaveanswers.append(answerline)
    saveanswers = sorted(saveanswers, key= lambda answer: len(answer.answers))
    notsaveanswers = sorted(notsaveanswers, key= lambda answer: len(answer.answers))
    answerlines = saveanswers + notsaveanswers

def solve(cellcount: int,answerlines: list[AnswerLine]) -> list[str]:
    for answerline in answerlines:
        answerline.answers = [x.upper() for x in answerline.answers]
    sortAnswers(answerlines)
    sortAnswerLines(answerlines)
    return solveAnswers(cellcount,answerlines)
