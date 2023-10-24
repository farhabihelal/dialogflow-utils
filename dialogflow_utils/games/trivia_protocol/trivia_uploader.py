import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "dialogflow_api", "src")
    )
)

import pandas as pd

from dialogflow import Dialogflow, Intent
from db.xlsx import read_xlsx

import re
from unidecode import unidecode

import google.cloud.dialogflow_v2 as dialogflow_v2


class TriviaUploader:
    def __init__(self, config: dict) -> None:
        self.configure(config)

        self.api = Dialogflow(config)

        self.db = {}
        self.trivia_data = {}

        self.valid_column_names = ["Trivia"]

    def configure(self, config: dict):
        self.config = config

    def process_trivias(self, db: dict = None) -> dict:
        db = db if db else self.db

        trivia_data = {}

        for sheet in db:
            df: pd.DataFrame = db[sheet]
            trivias = [str(x) if not pd.isna(x) else "" for x in df["Trivia"].tolist()]
            trivia_data[sheet] = trivias

        return trivia_data

    def load(self, db_path=None) -> dict:
        self.api.get_intents()
        self.api.generate_tree()

        db = read_xlsx(db_path)
        trivia_data = self.process_trivias(db=db)

        self.db = db
        self.trivia_data = trivia_data

        return trivia_data

    def process_intent_name(self, text: str) -> str:
        text = text.replace(" ", "-").lower().strip()
        text = re.sub(r"[^-\w\d]", "", unidecode(text))
        return text

    def upload(self, trivia_data: dict = None, language_code: str = None):
        trivia_data = trivia_data if trivia_data else self.trivia_data
        language_code = language_code if language_code else self.config["language_code"]

        # create trivia root intent node
        root_intent_obj = dialogflow_v2.Intent()
        root_intent_obj.display_name = self.process_intent_name("trivia")
        root_intent_obj.events = [root_intent_obj.display_name]
        root_intent_obj.priority = -1

        root_intent_obj: dialogflow_v2.Intent = self.api.create_intent(
            intent=root_intent_obj, language_code=language_code
        )

        # create trivia type intent and it's children
        for trivia_type in trivia_data:
            trivia_type: str
            type_intent_obj = dialogflow_v2.Intent()
            type_intent_obj.parent_followup_intent_name = root_intent_obj.name
            type_intent_obj.display_name = self.process_intent_name(trivia_type)
            type_intent_obj.events = [type_intent_obj.display_name]
            type_intent_obj.priority = -1

            type_intent_obj: dialogflow_v2.Intent = self.api.create_intent(
                type_intent_obj, language_code=language_code
            )

            trivias = trivia_data[trivia_type]
            trivia_intent_objs = []
            for i, trivia in enumerate(trivias):
                trivia: str
                trivia_intent_obj = dialogflow_v2.Intent()
                trivia_intent_obj.parent_followup_intent_name = type_intent_obj.name
                trivia_intent_obj.display_name = (
                    f"{type_intent_obj.display_name}-{i+1:03d}"
                )
                trivia_intent_obj.input_context_names = [
                    self.api.sessions_client.context_path(
                        self.api.project_id, "-", type_intent_obj.display_name
                    )
                ]
                trivia_intent_obj.events = [trivia_intent_obj.display_name]
                trivia_intent_obj.priority = -1

                trivia_intent_obj.messages = []
                msg = dialogflow_v2.Intent.Message()
                msg.text = dialogflow_v2.Intent.Message.Text(text=[trivia])
                trivia_intent_obj.messages.append(msg)

                trivia_intent_objs.append(trivia_intent_obj)

            result = self.api.batch_update_intents(
                intents=trivia_intent_objs, language_code=language_code
            )

    def postprocess_db_text(self, text):
        text = str(text)
        return text.strip()

    def run(self, db_path=None):
        db_path = db_path if db_path else self.config["db_path"]

        trivia_data = self.load(db_path=db_path)

        print("Backing up... ", end="")
        self.api.create_version(
            "back up before uploading trivia by country from api".title()
        )
        print("Done!")

        print("Uploader is running... ", end="")
        self.upload(trivia_data=trivia_data)
        print("Done!")


if __name__ == "__main__":
    base_dir = os.path.abspath(f"{os.path.dirname(__file__)}/../..")
    keys_dir = os.path.join(base_dir, ".temp/keys")
    data_dir = os.path.join(base_dir, "data")

    config = {
        "db_path": os.path.join(data_dir, "Haru Trivia Protocol.xlsx"),
        "credential": os.path.join(keys_dir, "haru-chat-games.json"),
        "language_code": "en",
    }

    uploader = TriviaUploader(config)
    uploader.run()
