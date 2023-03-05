import sys
import os

sys.path.append(os.path.abspath(f"{os.path.dirname(__file__)}/../../.."))

import json

from dialogflow_utils.parser.base import BaseParser

sys.path.append(os.path.abspath(f"{os.path.dirname(__file__)}/../.."))
from dialogflow_api.src.dialogflow import Intent


class JSONParser(BaseParser):
    def __init__(self, config: dict):
        super().__init__(config)

        self.data = None
        self.parsed_data = None

    def load(self, filepath: str = None) -> dict:
        filepath = filepath if filepath else self.config["filepath"]

        with open(filepath) as file:
            data = json.load(file)

        self.data = data
        return data

    def parse(self, data: dict) -> dict:
        data = data if data else self.data
        parsed_data = {}

        intents: list = data["intents"]

        for intent_data in intents:
            intent_data: dict
            intent: Intent = Intent.fromDict(intent_data)
            parsed_data[intent.display_name] = {
                "parent_name": intent_data["parent_name"],
                "intent": intent,
            }

        self.parsed_data = parsed_data
        return parsed_data

    def run(self, filepath: str = None) -> dict:
        data: dict = self.load(filepath)
        parsed_data: dict = self.parse(data)

        return parsed_data


if __name__ == "__main__":
    base_dir = os.path.abspath(f"{os.path.dirname(__file__)}/../../..")
    data_dir = os.path.join(base_dir, "data")
    keys_dir = os.path.join(base_dir, ".temp/keys")

    config = {
        "credential": os.path.join(keys_dir, "haru-test.json"),
        "filepath": os.path.join(data_dir, "simple.json"),
    }
    parser = JSONParser(config)
    parser.run()
