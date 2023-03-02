import pandas as pd
from madlibs_datarow import MadlibDataRow

from db.xlsx import read_xlsx


class MadlibsParser:
    def __init__(self, config: dict) -> None:
        self.configure(config)

    def configure(self, config: dict):
        self.config = config

    def load_db(self, db_path: str) -> dict:
        db_path = db_path if db_path else self.config["db_path"]
        db: dict = read_xlsx(db_path)
        self.db = db

        return db

    def process_db(self, db: dict = None, question_count: int = None) -> list:
        question_count = (
            question_count if question_count else self.config["question_count"]
        )

        db = db if db else self.db

        for sheet_name in db:
            sheet_name: str
            df: pd.DataFrame = db[sheet_name]

            titles = df["title"].tolist()
            questions = [
                df[f"question-{i}"].tolist() for i in range(1, question_count + 1)
            ]
            parameters = [
                df[f"parameter-{i}"].tolist() for i in range(1, question_count + 1)
            ]
            madlibs = df["madlib"].tolist()

            return [
                MadlibDataRow.fromDict(
                    {
                        "title": title,
                        "questions": [questions[j][i] for j in range(question_count)],
                        "parameters": [parameters[j][i] for j in range(question_count)],
                        "madlib": madlib,
                    }
                )
                for i, title, madlib, in zip(range(len(titles)), titles, madlibs)
            ]

    def run(self, db_path: str = None, question_count: int = None) -> list:
        db: dict = self.load_db(db_path)
        db_data = self.process_db(db, question_count)
        return db_data
