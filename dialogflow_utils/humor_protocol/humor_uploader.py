import sys
import os

sys.path.append(os.path.abspath(f"{os.path.dirname(__file__)}/.."))

import pandas as pd

from dialogflow_api.src.dialogflow import Dialogflow, Intent

import google.cloud.dialogflow_v2 as dialogflow_v2

from db.xlsx import read_xlsx


class HumorUploader:
    def __init__(self, config: dict) -> None:
        self.configure(config)

        self.api = Dialogflow(config)

        self.db = {}
        self.humor_data = {}

        self.valid_column_names = ["Setup", "Punchline"]

    def configure(self, config: dict):
        self.config = config

    def process_humors(self, db: dict = None) -> dict:
        db = db if db else self.db

        humor_data = {}

        for sheet in db:
            df = db[sheet]
            setups = df["Setup"].tolist()
            punchlines = df["Punchline"].tolist()

            humor_data[sheet] = [
                (self.postprocess_db_text(x), self.postprocess_db_text(y))
                for x, y in zip(setups, punchlines)
            ]
        return humor_data

    def load(self, db_path=None) -> dict:
        self.api.get_intents()
        self.api.generate_tree()

        db = read_xlsx(db_path)
        humor_data = self.process_humors(db=db)

        self.db = db
        self.humor_data = humor_data

        return humor_data

    def process_intent_name(self, text: str) -> str:
        return text.replace(" ", "-").lower().strip()

    def upload(self, humor_data: dict = None, language_code: str = None):
        humor_data = humor_data if humor_data else self.humor_data
        language_code = language_code if language_code else self.config["language_code"]

        # create humor root intent node
        root_intent_obj = dialogflow_v2.Intent()
        root_intent_obj.display_name = self.process_intent_name("humor")
        root_intent_obj.events = [root_intent_obj.display_name]
        root_intent_obj.priority = -1

        root_intent_obj: dialogflow_v2.Intent = self.api.create_intent(
            intent=root_intent_obj, language_code=language_code
        )

        # create humor type intent and it's children
        for humor_type in humor_data:
            humor_type: str
            type_intent_obj = dialogflow_v2.Intent()
            type_intent_obj.parent_followup_intent_name = root_intent_obj.name
            type_intent_obj.display_name = self.process_intent_name(humor_type)
            type_intent_obj.events = [type_intent_obj.display_name]
            type_intent_obj.priority = -1

            type_intent_obj: dialogflow_v2.Intent = self.api.create_intent(
                type_intent_obj, language_code=language_code
            )

            humors = humor_data[humor_type]
            humor_intent_objs = []
            for i, humor in enumerate(humors):
                humor: tuple
                humor_intent_obj = dialogflow_v2.Intent()
                humor_intent_obj.parent_followup_intent_name = type_intent_obj.name
                humor_intent_obj.display_name = (
                    f"{type_intent_obj.display_name}-{i+1:03d}"
                )
                humor_intent_obj.input_context_names = [
                    self.api.sessions_client.context_path(
                        self.api.project_id, "-", type_intent_obj.display_name
                    )
                ]
                humor_intent_obj.events = [humor_intent_obj.display_name]
                humor_intent_obj.priority = -1

                humor_intent_obj.messages = []
                for x in humor:
                    x: str
                    msg = dialogflow_v2.Intent.Message()
                    msg.text = dialogflow_v2.Intent.Message.Text(text=[x])
                    humor_intent_obj.messages.append(msg)

                humor_intent_objs.append(humor_intent_obj)

            result = self.api.batch_update_intents(
                intents=humor_intent_objs, language_code=language_code
            )

    def postprocess_db_text(self, text):
        text = str(text)
        return text.strip()

    def run(self, db_path=None):
        db_path = db_path if db_path else self.config["db_path"]

        humor_data = self.load(db_path=db_path)

        print("Uploader is running... ", end="")
        self.upload(humor_data=humor_data)
        print("Done!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--db_path", dest="db_path", type=str, help="Books database path"
    )

    parser.add_argument(
        "--project_id", dest="project_id", type=str, help="Google Cloud Project Id"
    )
    parser.add_argument(
        "--credential",
        dest="credential",
        type=str,
        help="Path to Google Cloud Project credential",
    )

    args = parser.parse_args()

    # config = {
    #     "db_path": args.db_path,
    #     "credential": args.credential,
    # }

    base_dir = os.path.abspath(f"{os.path.dirname(__file__)}/../..")
    keys_dir = os.path.join(base_dir, ".temp/keys")
    data_dir = os.path.join(base_dir, "data")

    config = {
        "db_path": os.path.join(data_dir, "Haru Humor Protocol.xlsx"),
        "credential": os.path.join(keys_dir, "haru-chat-games.json"),
        "language_code": "en",
    }

    uploader = HumorUploader(config)
    uploader.run()
