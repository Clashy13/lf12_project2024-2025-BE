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

def sortedConnectedAnswerIndexes(indexes: list[int], answers: list[AnswerLine], solution: list[str]) -> list[int]:
    return sorted(indexes, key= lambda idx : sum(1 for cellidx in answers[idx].cellindexes if solution[cellidx] != "" ))

def finalSolution(solution: list[str]) -> bool:
    return solution.count("") < len(solution) * 0.5

def getSolutions(answeridx: int, answers: list[AnswerLine], filledansweridxs: list[int], solution: list[str]) -> list[list[str]]:
    global starttime
    if time.time() - starttime > 20:
        raise Exception("Error while running solve algorithm: took too long due to too many empty answers")
    totalsolutions = []
    answer = answers[answeridx]
    cellidxs = answer.cellindexes
    for word in answer.answers:
        if not wordFits(word,cellidxs,solution):
            continue

        newsolution = createSolutionWithWord(word,cellidxs,solution)
        newfilledansweridxs = filledansweridxs + [answeridx]

        connectedanswersidxs = filterConnectedAnswerIndexes(answers,newfilledansweridxs,newsolution)
        sortedansweridxs = sortedConnectedAnswerIndexes(connectedanswersidxs,answers,newsolution)

        solutions = []
        for i in sortedansweridxs:
            localsolutions = getSolutions(i,answers,newfilledansweridxs,newsolution)
            solutions.extend(localsolutions)
            final = False
            for s in localsolutions:
                if finalSolution(s):
                    final = True
                    break
            if final:
                break
        
        if not solutions:
            solutions = [newsolution]
        
        totalsolutions.extend(solutions)

    return totalsolutions

def solveAnswers(cellcount: int, answers: list[AnswerLine]) -> list[str]:
    answers = sorted(answers, key= lambda answer: -countAnswerConnections(answers, answers.index(answer) ))
    global starttime
    starttime = time.time()
    emptysolution = ["" for i in range(cellcount)]
    solutions: list[list] = []
    for i in range(len(answers)):
        solutions.extend(getSolutions(i,answers,[],emptysolution.copy()))

    bestsolution = min(solutions, key= lambda solution: solution.count(""))
    return bestsolution

def solve(cellcount: int,answerlines: list[AnswerLine]) -> list[str]:
    for answerline in answerlines:
        answerline.answers = [x.lower() for x in answerline.answers]
    return solveAnswers(cellcount,answerlines)
