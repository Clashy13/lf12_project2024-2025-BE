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

def main():
    # cellcount = 11
    # answers = [{"CellIndexes": [0,3,7,9],"Answers":["tuna"]},
    #            {"CellIndexes": [2,3,4,5,6],"Answers":["music"]},
    #            {"CellIndexes": [1,5],"Answers":["hi"]},
    #            {"CellIndexes": [6,8,10],"Answers":["can"]}]
    
    # cellcount = 25
    # answers = [{"CellIndexes": [0,1,2,3,4],"Answers":["GRADE"]},
    #            {"CellIndexes": [5,6,7,8,9],"Answers":["LOVED"]},
    #            {"CellIndexes": [10,11,12,13,14],"Answers":["AMONG"]},
    #            {"CellIndexes": [15,16,17,18,19],"Answers":["RAISE"]},
    #            {"CellIndexes": [20,21,22,23,24],"Answers":["ENDED"]},
    #            {"CellIndexes": [0,5,10,15,20],"Answers":["GLARE"]},
    #            {"CellIndexes": [1,6,11,16,21],"Answers":["ROMAN"]},
    #            {"CellIndexes": [2,7,12,17,22],"Answers":["AVOID"]},
    #            {"CellIndexes": [3,8,13,18,23],"Answers":["DENSE"]},
    #            {"CellIndexes": [4,9,14,19,24],"Answers":["EDGED"]},]
    answers = [{'CellIndexes': [3, 4, 5, 6], 'Answers': ['Hose', 'Albe', 'Baji', 'Body', 'Bogu', 'Capa', 'Cape', 'Faja', 'Gala', 'Geta', 'Gurt', 'Haik', 'Helm', 'Hemd', 'Hosl', 'Jock', 'Jupe', 'Kapu', 'Kilt', 'Kira', 'Mode', 'Muff', 'Ngop', 'Pelz', 'Ring', 'Robe', 'Rock', 'Sari', 'Slip', 'Sock', 'Tabi', 'Teil', 'Toga', 'Tuch', 'Tutu', 'Wams']},
               {'CellIndexes': [4, 11, 18, 25, 32, 38, 46, 53], 'Answers': ['Ohnmacht']},
               {'CellIndexes': [5, 12, 19], 'Answers': ['Sie']}, 
               {'CellIndexes': [0, 6, 13, 20, 26, 34, 39, 48, 54], 'Answers': ['zerfallen']}, 
               {'CellIndexes': [1, 7, 15, 21, 28], 'Answers': ['Pfeil']}, 
               {'CellIndexes': [2, 9, 16, 23], 'Answers': ['Orca', 'Orka']}, 
               {'CellIndexes': [7, 8, 9, 10], 'Answers': ['Furt']}, 
               {'CellIndexes': [11, 12, 13, 14, 15], 'Answers': []}, 
               {'CellIndexes': [22, 29, 35, 42, 50, 57], 'Answers': []}, 
               {'CellIndexes': [24, 30, 37, 44, 52], 'Answers': ['Idaho', 'Maine', 'Texas']}, 
               {'CellIndexes': [21, 22, 23, 24], 'Answers': ['Imam', 'Iman']}, 
               {'CellIndexes': [17, 18, 19, 20], 'Answers': []}, 
               {'CellIndexes': [26, 27, 28, 29], 'Answers': ['Aula']}, 
               {'CellIndexes': [36, 43, 51, 58], 'Answers': ['Rede']}, 
               {'CellIndexes': [41, 49, 56], 'Answers': []}, 
               {'CellIndexes': [35, 36, 37], 'Answers': ['Uri', 'Zug']}, 
               {'CellIndexes': [31, 32, 33, 34], 'Answers': ['Agag', 'Ahab', 'Amon', 'Amri', 'Amun', 'Baal', 'Bela', 'Jehu', 'Joas', 'Mesa', 'Omri', 'Phul', 'Saul', 'Thou']}, 
               {'CellIndexes': [39, 40, 41, 42, 43, 44], 'Answers': ['Lotsen']}, 
               {'CellIndexes': [49, 50, 51, 52], 'Answers': ['Oede']}, 
               {'CellIndexes': [45, 46, 47, 48], 'Answers': ['Ahle']}, 
               {'CellIndexes': [54, 55, 56, 57, 58], 'Answers': ['Nonne']}]
    cellcount = 59

    for answer in answers:
        answer["Answers"] = [x.lower() for x in answer["Answers"]]
    
    bestsolution = solveAnswers(cellcount,answers)
    st = ""
    for c in bestsolution:
        st += c
        if c == "":
            st += " "
    print("'"+st+"'")
    
main()