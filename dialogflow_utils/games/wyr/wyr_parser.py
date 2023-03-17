import pandas as pd
from wyr_datarow import WYRDataRow

from db.xlsx import read_xlsx


class WYRParser:
    def __init__(self, config: dict) -> None:
        self.configure(config)

    def configure(self, config: dict):
        self.config = config

    def load_db(self, db_path: str) -> dict:
        db_path = db_path if db_path else self.config["db_path"]
        db: dict = read_xlsx(db_path)
        self.db = db

        return db

    def process_db(self, db: dict = None) -> list:

        db = db if db else self.db

        for sheet_name in db:
            sheet_name: str
            df: pd.DataFrame = db[sheet_name]

            choices = df["choice"].tolist()
            responses = df["response"].tolist()

            return [
                WYRDataRow(
                    choice=choice,
                    response=response,
                )
                for choice, response, in zip(choices, responses)
            ]

    def run(self, db_path: str = None) -> list:
        db: dict = self.load_db(db_path)
        db_data = self.process_db(db)
        return db_data
