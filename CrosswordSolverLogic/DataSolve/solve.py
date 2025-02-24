from . import  AnswerLine

def countAnswerConnections(answers: list, idx: int) -> int:
    count = 0
    for cellidx in answers[idx]["CellIndexes"]:
        for i,answer in enumerate(answers):
            if idx != i and cellidx in answer["CellIndexes"]:
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

def filterConnectedAnswerIndexes(answers: list, filledansweridxs: list[int], solution: list[str]) -> list:
    filtered = []
    for i,answer in enumerate(answers):
        if i in filledansweridxs:
            continue
        connected = False
        for othercellidx in answer["CellIndexes"]:
            if solution[othercellidx] != "":
                connected = True
                break
        if connected:
            filtered.append(i)
    return filtered

def sortedConnectedAnswerIndexes(indexes: list[int], answers: list, solution: list[str]) -> list[int]:
    return sorted(indexes, key= lambda idx : sum(1 for cellidx in answers[idx]["CellIndexes"] if solution[cellidx] != "" ))

def finalSolution(solution: list[str]) -> bool:
    return solution.count("") < len(solution) * 0.5

def getSolutions(answeridx: int, answers: list, filledansweridxs: list[int], solution: list[str]) -> list[list[str]]:
    totalsolutions = []
    answer = answers[answeridx]
    cellidxs = answer["CellIndexes"]
    for word in answer["Answers"]:
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

def solveAnswers(cellcount: int, answers: list) -> list[str]:
    answers = sorted(answers, key= lambda answer: -countAnswerConnections(answers, answers.index(answer) ))

    emptysolution = ["" for i in range(cellcount)]
    solutions: list[list] = []
    for i in range(len(answers)):
        solutions.extend(getSolutions(i,answers,[],emptysolution.copy()))

    bestsolution = min(solutions, key= lambda solution: solution.count(""))
    return bestsolution

def solve(cellcount: int,answerlines: list[AnswerLine]) -> list[str]:
    for answerline in answerlines:
        answerline = [x.lower() for x in answerline.answers]
    return solveAnswers(cellcount,answerlines)
