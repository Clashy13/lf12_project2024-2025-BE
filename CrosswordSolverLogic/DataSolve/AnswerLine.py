class AnswerLine:
    def __init__(self, answers: list[str], cellindexes: list[int], similarity: float):
        self.answers = answers
        self.cellindexes = cellindexes
        self.similarity = similarity
