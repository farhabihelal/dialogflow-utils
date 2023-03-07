import sys
import os

sys.path.append(os.path.abspath(f"{os.path.dirname(__file__)}/.."))

from dialogflow_api.src.dialogflow import Dialogflow, Intent

import google.cloud.dialogflow_v2 as dialogflow_v2

sys.path.append(os.path.abspath(f"{os.path.dirname(__file__)}/../.."))
from dialogflow_utils.parser.tree.json_parser import JSONParser


class IntentTreeCreator:
    def __init__(self, config: dict) -> None:
        self.config = config

        self.api = Dialogflow(config)
        self.api.get_intents()
        self.api.generate_tree()

        self.parser = self.get_parser(self.config)

    def get_parser(self, config: dict):
        return JSONParser(config)

    def generate_tree(self, parsed_data: dict) -> Intent:
        """
        Must have only one root node without parent or the parent is in the global tree.
        """
        root_intent = None

        for intent_name in parsed_data:
            intent_name: str

            intent: Intent = parsed_data[intent_name]["intent"]
            parent_name: str = parsed_data[intent_name]["parent_name"]

            parent_data: dict = parsed_data.get(parent_name)
            if not parent_data:
                # mark this intent as the root for this subtree
                root_intent = intent

                # check if parent is in the global tree
                parent: Intent = self.api.intents["display_name"].get(parent_name)
                if parent:
                    intent._parent = parent

                continue

            parent: Intent = parent_data["intent"]
            intent._parent = parent
            parent._children.append(intent)

        return root_intent

    def create_tree(self, root_intent: Intent, language_code=None):
        intents_to_create = [root_intent]

        while len(intents_to_create) > 0:
            intent: Intent = intents_to_create.pop(0)
            parent: Intent = intent.parent
            if parent:
                self.api.create_child(intent, parent, language_code=language_code)
            else:
                intent_obj = self.api.create_intent(
                    intent.intent_obj, language_code=language_code
                )
                intent._intent_obj = intent_obj
            intents_to_create.extend(intent.children)

    def run(self, filepath: str = None):
        parsed_data = self.parser.run(filepath)
        root_intent: Intent = self.generate_tree(parsed_data)
        self.create_tree(root_intent)


if __name__ == "__main__":
    base_dir = os.path.abspath(f"{os.path.dirname(__file__)}/../..")
    data_dir = os.path.join(base_dir, "data")
    keys_dir = os.path.join(base_dir, ".temp/keys")

    config = {
        "credential": os.path.join(keys_dir, "haru-test.json"),
        "filepath": os.path.join(data_dir, "simple.json"),
    }

    creator = IntentTreeCreator(config)
    creator.run()
