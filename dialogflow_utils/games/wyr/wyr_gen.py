import os
import sys

sys.path.append(os.path.abspath(f"{os.path.dirname(__file__)}/.."))

sys.path.append(os.path.abspath(f"{os.path.dirname(__file__)}/../.."))
from dialogflow_api.src.dialogflow import Dialogflow, Intent

import google.cloud.dialogflow_v2 as dialogflow_v2

from wyr_datarow import WYRDataRow
from wyr_parser import WYRParser

import re


class WYRGenerator:
    def __init__(self, config: dict) -> None:
        self.configure(config)

        self.parser = WYRParser(config)

        self.api = Dialogflow(config)
        self.api.get_intents()
        self.api.generate_tree()

    def configure(self, config: dict):
        self.config = config

    def create_wyrs(
        self,
        wyr_data: list,
        parent_intent_name: str = None,
        language_code: str = None,
    ):

        parent = (
            self.api.intents["display_name"][parent_intent_name]
            if parent_intent_name
            else None
        )

        wyr_root_intent_name = "would-you-rather-choices"

        root_intent_obj = (
            dialogflow_v2.Intent()
            if not self.api.intents["display_name"].get(wyr_root_intent_name)
            else self.api.intents["display_name"][wyr_root_intent_name].intent_obj
        )
        root_intent_obj.display_name = wyr_root_intent_name
        root_intent_obj.events = [root_intent_obj.display_name]
        root_intent_obj.priority = 0

        root_intent = Intent(root_intent_obj)

        if parent:
            self.api.create_child(
                intent=root_intent, parent=parent, language_code=language_code
            )
        else:
            root_intent_obj: dialogflow_v2.Intent = (
                self.api.create_intent(
                    intent=root_intent_obj, language_code=language_code
                )
                if not self.api.intents["display_name"].get(
                    root_intent_obj.display_name
                )
                else self.api.update_intent(
                    intent=root_intent_obj, language_code=language_code
                )
            )

        wyr_intents = []

        # add choice intents
        for i, wyr in enumerate(wyr_data):
            wyr: WYRDataRow

            intent_obj = dialogflow_v2.Intent()
            intent_obj.display_name = f"{root_intent_obj.display_name}-choice-{i+1}"
            intent_obj.events = [intent_obj.display_name]
            intent_obj.parent_followup_intent_name = root_intent_obj.name
            intent_obj.action = "would-you-rather-outro"

            # Any Param 1
            intent_obj.parameters = []
            parameter = dialogflow_v2.Intent.Parameter()
            parameter.display_name = f"any"
            parameter.default_value = ""
            parameter.entity_type_display_name = "@sys.any"
            parameter.is_list = False
            parameter.mandatory = False
            parameter.value = f"${parameter.display_name}"
            intent_obj.parameters.append(parameter)

            # Any Param 2
            parameter = dialogflow_v2.Intent.Parameter()
            parameter.display_name = f"any1"
            parameter.default_value = ""
            parameter.entity_type_display_name = "@sys.any"
            parameter.is_list = False
            parameter.mandatory = False
            parameter.value = f"${parameter.display_name}"
            intent_obj.parameters.append(parameter)

            # Training Data
            intent_obj.training_phrases = self.get_training_data(wyr.choice)

            intent_obj.messages = []
            payload = {
                "would-you-rather": {
                    "choice": f"{wyr.choice.lower()}",
                },
            }
            intent_obj.messages.append(dialogflow_v2.Intent.Message(payload=payload))
            intent_obj.messages.append(
                dialogflow_v2.Intent.Message(
                    text=dialogflow_v2.Intent.Message.Text(text=[wyr.response])
                )
            )

            intent = Intent(intent_obj)
            wyr_intents.append(intent)

        # fallback
        fallback_intent_obj = dialogflow_v2.Intent()
        fallback_intent_obj.display_name = (
            f"{root_intent_obj.display_name}-choice-fallback"
        )
        fallback_intent_obj.events = [fallback_intent_obj.display_name]
        fallback_intent_obj.parent_followup_intent_name = root_intent_obj.name
        fallback_intent_obj.action = "would-you-rather-outro"
        fallback_intent_obj.is_fallback = True

        fallback_intent_obj.messages = [
            dialogflow_v2.Intent.Message(
                text=dialogflow_v2.Intent.Message.Text(
                    text=["Nice choice!", "Great choice!"]
                )
            ),
            dialogflow_v2.Intent.Message(
                text=dialogflow_v2.Intent.Message.Text(
                    text=[
                        "I would've rather chosen to #globals.wyr_choice_fallback.",
                        "I would rather choose to #globals.wyr_choice_fallback.",
                    ]
                )
            ),
        ]
        fallback_intent = Intent(fallback_intent_obj)
        wyr_intents.append(fallback_intent)

        self.api.create_children(
            intents=wyr_intents, parent=root_intent, language_code=language_code
        )

    def create_wyr_intro(self):
        pass

    def get_training_data(self, text: str) -> list:
        training_data = []

        ngrams = generate_ngrams_range(text, start=3)

        for ngram in ngrams:
            ngram: str
            training_phrase = dialogflow_v2.Intent.TrainingPhrase()

            any = dialogflow_v2.Intent.TrainingPhrase.Part()
            any.text = f"ANY"
            any.user_defined = True
            any.alias = "any"
            any.entity_type = "@sys.any"

            part = dialogflow_v2.Intent.TrainingPhrase.Part()
            part.text = f" {ngram} "
            part.user_defined = True

            any1 = dialogflow_v2.Intent.TrainingPhrase.Part()
            any1.text = f"ANY"
            any1.user_defined = True
            any1.alias = "any1"
            any1.entity_type = "@sys.any"

            training_phrase.parts = [any, part, any1]
            training_data.append(training_phrase)

        return training_data

    def run(
        self,
        db_path: str = None,
        parent_intent_name: str = None,
        language_code: str = None,
    ):
        wyr_data: list = self.parser.run(db_path=db_path)
        self.create_wyrs(
            wyr_data=wyr_data,
            parent_intent_name=parent_intent_name
            if parent_intent_name
            else self.config["parent_intent_name"],
            language_code=language_code
            if language_code
            else self.config["language_code"],
        )


def generate_ngrams(text: str, n: int):
    # Convert to lowercases
    text = text.lower()

    # Replace all none alphanumeric characters with spaces
    text = re.sub(r"[^a-zA-Z0-9\s]", " ", text)

    # Break sentence in the token, remove empty tokens
    tokens = [token for token in text.split(" ") if token != ""]

    # Use the zip function to help us generate n-grams
    # Concatentate the tokens into ngrams and return
    ngrams = zip(*[tokens[i:] for i in range(n)])
    return [" ".join(ngram) for ngram in ngrams]


def generate_ngrams_range(text: str, start: int = 1, end: int = -1):
    end = end if end > 0 else len(text)
    return [x for i in range(start, end) for x in generate_ngrams(text, i)]


if __name__ == "__main__":
    base_dir = os.path.abspath(f"{os.path.dirname(__file__)}/../../..")
    keys_dir = os.path.join(base_dir, ".temp/keys")
    data_dir = os.path.join(base_dir, "data")

    config = {
        "db_path": os.path.join(data_dir, "would-you-rather-scripts.xlsx"),
        "credential": os.path.join(keys_dir, "haru-test.json"),
        "parent_intent_name": "would-you-rather-tells-choices",
        "language_code": "en",
    }
    gen = WYRGenerator(config)
    gen.run()
