import sys
import os

sys.path.append(os.path.abspath(f"{os.path.dirname(__file__)}/.."))

from dialogflow_api.src.dialogflow import Dialogflow
from google.cloud.dialogflow import Intent, Context

from csv_parser import CSVParser

from uuid import uuid4, uuid5


class IntentTreeCreator:
    def __init__(self, config: dict) -> None:
        self.config = config

        self.dialogflow = Dialogflow(config["dialogflow"])
        # self.dialogflow.get_intents()
        self.parser = CSVParser(config["parser"])

        self.intents = None

    def create_tree(self, intents: list = None):
        self.create_intents(intents)
        pass

    def create_intents(self, intents: list = None):
        intents = intents if intents else self.intents

        df_intents = []
        for intent in intents:
            df_intent = Intent()
            # df_intent.name = f"projects/project_id/agent/intents/{uuid5().hex}"
            df_intent.display_name = intent.display_name
            df_intent.events = []
            # df_intent.followup_intent_info = None
            df_intent.input_context_names = None
            df_intent.output_contexts = None
            df_intent.messages = []
            df_intent.parameters = []
            df_intent.root_followup_intent_name = None
            df_intent.training_phrases = []
            df_intent.action = ""
            df_intent.end_interaction = False

            df_intents.append(df_intent)

        print(df_intents)

    def upload(self, intents: list = None):
        pass

    def run(self):
        self.parser.run()
        self.intents = self.parser.intents
        self.create_tree()
        self.upload()


if __name__ == "__main__":
    data_dir = os.path.abspath(f"{os.path.dirname(__file__)}/data")
    keys_dir = os.path.abspath(f"{os.path.dirname(__file__)}/../../.temp/keys")

    config = {
        "dialogflow": {
            "project_id": "api-test-v99y",
            "credential": f"{keys_dir}/api-test.json",
        },
        "parser": {
            "filepath": f"{data_dir}/sample.tsv",
        },
    }

    creator = IntentTreeCreator(config)
    creator.run()
