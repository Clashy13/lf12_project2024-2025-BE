import json
import requests
import time

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from typing import List, Dict
from urllib.parse import urlparse

from CrosswordSolverLogic.CollectiveCellData import QuestionLine
from CrosswordSolverLogic.DataSolve import AnswerLine
from CrosswordSolverLogic.DataSolve.QuestionURLMatcher import QuestionURLMatcher

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
            cleaned_question = QuestionURLMatcher.cleanQuestion(question_line.question)
            new_question = QuestionURLMatcher.matchedQuestion(cleaned_question)
            url_question = new_question.replace(" ","-")
            similarity = QuestionURLMatcher.similarity(cleaned_question, new_question)
            list_of_answers = self._get_answers(
                url_question, len(question_line.cellindexes)
            )
            answers.append(AnswerLine(list_of_answers, question_line.cellindexes, similarity))
            time.sleep(0.001)  # Avoid accidentally DDOSing the site
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

        try:
            url = self._get_url(question)
            response = self._get_response(url)
            if not response.history or response.history[0].status_code != 302:
                return self._response_to_answers(response, question, word_length)
            return []

        except requests.RequestException as e:
            raise ConnectionError(f"Failed to fetch answers: {str(e)}")

    def _get_url(self, question: str) -> str:
        return f"{self.BASE_URL}{question}.html"
    
    def _get_response(self, url: str) -> requests.Response:
        response = self.session.get(url, timeout=60)
        response.raise_for_status()
        return response

    def _response_to_answers(
        self, response: requests.Response, question: str, word_length: int
    ) -> list[str]:
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

    def _filter_by_length(self, answers: Dict, length: int) -> Dict:
        return dict(filter(lambda x: x[0] == str(length), answers.items()))

    def _extract_answer_words(self, filtered_answers: Dict, length: int) -> List[str]:
        if str(length) not in filtered_answers:
            return []
        return list(filtered_answers[str(length)].keys())


def main():
    try:
        answers = CrosswordScraper().scrap([QuestionLine("laubbaum", [0, 1, 2, 3])])
        print(answers[0].answers)
    except (ValueError, ConnectionError) as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
