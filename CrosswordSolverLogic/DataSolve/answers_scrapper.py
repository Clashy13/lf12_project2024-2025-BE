from bs4 import BeautifulSoup
from typing import List, Dict
import json
import re
import requests
import time

from CrosswordSolverLogic.CollectiveCellData import QuestionLine
from CrosswordSolverLogic.DataSolve import AnswerLine


class CrosswordScraper:
    def __init__(self):
        self.session = requests.Session()
        self.BASE_URL = self._load_base_url()

    def _load_base_url(self) -> str:
        with open("config.txt", "r") as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith("#"):
                    return line
        raise ValueError("config.txt not found")

    def scrap(self, question_lines: List[QuestionLine]) -> list[AnswerLine]:
        answers = []
        for question_line in question_lines:
            list_of_answers = self._get_answers(
                question_line.question, len(question_line.cellindexes)
            )
            answers.append(AnswerLine(list_of_answers, question_line.cellindexes))
            time.sleep(2)  # Avoid accidentally DDOSing the site
        print([a.answers for a in answers])
        return answers

    def _get_answers(self, question: str, word_length: int) -> List[str]:
        """
        Fetches answers for a given question and word length.

        Args:
            question: The crossword question/hint
            word_length: Expected length of the answer

        Returns:
            List of possible answers
        """
        if not question or not isinstance(word_length, int) or word_length < 1:
            raise ValueError("Invalid question or word length")

        question = self._replace_special_chars(question)
        url = f"{self.BASE_URL}{question}.html"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")
            answers_payload = soup.find("div", {"data-answers": True})

            if not answers_payload or len(answers_payload) == 0:  # type: ignore
                print(
                    f"\033[93mWarning: Couldn't find the page for question '{question}'\033[0m"
                )
                return []

            answers_json = json.loads(answers_payload["data-answers"])  # type: ignore
            filtered_answers = self._filter_by_length(answers_json, word_length)

            return self._extract_answer_words(filtered_answers, word_length)

        except requests.RequestException as e:
            raise ConnectionError(f"Failed to fetch answers: {str(e)}")

    def _filter_by_length(self, answers: Dict, length: int) -> Dict:
        return dict(filter(lambda x: x[0] == str(length), answers.items()))

    def _extract_answer_words(self, filtered_answers: Dict, length: int) -> List[str]:
        if str(length) not in filtered_answers:
            return []
        return list(filtered_answers[str(length)].keys())

    # Note - Question with 2 words might cause trouble
    def _replace_special_chars(self, input_string):
        sanitized_string = re.sub(r"[^a-zA-Z0-9äüöÄÜÖ]", "-", input_string)
        sanitized_string = re.sub(r"-+", "-", sanitized_string)
        return sanitized_string.strip("-")

def main():
    try:
        answers = CrosswordScraper().scrap([QuestionLine("laubbaum", [0, 1, 2, 3])])
        print(answers[0].answers)
    except (ValueError, ConnectionError) as e:
        print(f"Error: {str(e)}")
 
 
if __name__ == "__main__":
    main()