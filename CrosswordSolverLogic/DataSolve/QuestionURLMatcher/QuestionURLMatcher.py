from sentence_transformers import SentenceTransformer
import faiss
import re
import spacy

dir = "CrosswordSolverLogic/DataSolve/QuestionURLMatcher/"
nlp = spacy.load("de_core_news_lg")
model = SentenceTransformer("sentence-transformers/gtr-t5-large") # type: ignore
f = open(dir + "questions.txt","r")
questions = f.read().split("\n")
f.close()
index = faiss.read_index(dir + "index.faiss")
index.nprobe = 1000 # increases precision but causes server to take longer to load

def cleanQuestion(question: str) -> str:
    question = question.lower()
    question = re.sub(r"[^a-z0-9äüöß\.]", " ", question)
    question = re.sub(r"-+", " ", question)
    question = re.sub(r" +", " ", question)
    question = re.sub(r"\.+", ".", question)
    question = re.sub(r" \.", " ", question)
    question = question.strip()
    return question

def matchedQuestion(question: str ) -> str:
    embedding = model.encode([question])
    D, I = index.search(embedding, 1)
    return str(questions[I[0][0]])

def similarity(q1: str, q2: str) -> float:
    return nlp(q1).similarity(nlp(q2))
