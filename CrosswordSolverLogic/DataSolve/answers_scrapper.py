from bs4 import BeautifulSoup
from typing import List, Dict
import json
import re
import requests
import time
import os
from groq import Groq
from dotenv import load_dotenv

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
            time.sleep(0.2)  # Avoid accidentally DDOSing the site
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

        oldquestion = question

        try:
            answers = self._respond_answers(question,word_length)
            if answers is not None:
                return answers
            
            # corrected_question = self._AI_spell_check(question)
            # if corrected_question:
            #     print(corrected_question)
            #     answers = self._respond_answers(corrected_question,word_length)
            #     if answers is not None:
            #         return answers
            
            return self._get_sub_answers(oldquestion, word_length)

        except requests.RequestException as e:
            raise ConnectionError(f"Failed to fetch answers: {str(e)}")

    def _get_sub_answers(self, question: str, word_length: int) -> List[str]:
        answers = []
        if "," in question or ";" in question:
            questions = re.split(",|;", question)
            questions = [self._replace_special_chars(q) for q in questions]
            if "" not in questions:
                for qst in questions:
                    url = f"{self.BASE_URL}{qst}.html"
                    resp = self._get_response(url)
                    if resp.history and resp.history[0].status_code == 302:
                        continue
                    answers.extend(self._response_to_answers(resp, qst, word_length))
        return answers

    def _respond_answers(self, question: str, word_length: int) -> list[str] | None:
        question = self._replace_special_chars(question)
        url = f"{self.BASE_URL}{question}.html"
        response = self._get_response(url)
        if not response.history or response.history[0].status_code != 302:
            return self._response_to_answers(response, question, word_length)
        return None
    
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

    def _replace_special_chars(self, input_string):
        sanitized_string = re.sub(r"[^a-zA-Z0-9äüöÄÜÖ]", "-", input_string)
        sanitized_string = re.sub(r"-+", "-", sanitized_string)
        return sanitized_string.strip("-")

    def _AI_spell_check(self, question: str) -> str | None:
        load_dotenv()
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("\033[93mWarning: API key not found\033[0m")
            return question

        client = Groq(api_key=api_key)
        prompt = (
            "Agiere als Rechtschreibkorrektor. Korrigiere alle falsch geschriebenen. Ohne Kommentar zu geben. "
            "Wörter in Fragen, aber lasse alle Sonderzeichen, Satzzeichen und "
            "Formatierungen unverändert."
            "Erhalte die Groß- und Kleinschreibung bei, wo es "
            "notwendig ist. Beispiel input: 'groß; gejb' -> 'groß; gelb'"
        )
        resp = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": question},
            ],
        )

        return resp.choices[0].message.content


def main():
    try:
        answers = CrosswordScraper().scrap([QuestionLine("laubbaum", [0, 1, 2, 3])])
        print(answers[0].answers)
    except (ValueError, ConnectionError) as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
