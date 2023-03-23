import os
import sys

sys.path.append(os.path.abspath(f"{os.path.dirname(__file__)}/.."))

from dialogflow_api.src.dialogflow import Dialogflow, Intent

import google.cloud.dialogflow_v2 as dialogflow_v2

from time import sleep

from sentiment.sentiment_gen_unsafe import SentimentGeneratorUnsafe


class EntityDetectorGenerator:
    def __init__(self, config: dict) -> None:
        self.configure(config)

        self.api = self.config.get("api")
        if not self.api:
            self.api = Dialogflow(config)
            self.api.get_intents()
            self.api.generate_tree()

    def configure(self, config: dict):
        self.config = config

    def create_entity_detector(self, parent: Intent, language_code: str = None):

        # capture node
        capture_intent_obj = dialogflow_v2.Intent()
        capture_intent_obj.display_name = f"{parent.display_name}-entity-capture"
        capture_intent_obj.events = [capture_intent_obj.display_name]
        capture_intent_obj.action = f""
        capture_intent_obj.messages = [
            dialogflow_v2.Intent.Message(payload={"local_entity_detection": ""})
        ]

        parameter = dialogflow_v2.Intent.Parameter()
        parameter.display_name = "any"
        parameter.entity_type_display_name = "@sys.any"
        parameter.mandatory = True
        parameter.is_list = False
        parameter.value = "#globals.tner_any"
        parameter.default_value = ""
        parameter.prompts = ["I'm sorry! I couldn't get that."]

        capture_intent_obj.parameters = [parameter]

        capture_intent = Intent(capture_intent_obj)
        capture_intent = self.api.create_child(
            intent=capture_intent, parent=parent, language_code=language_code
        )

        # capture success node
        capture_success_intent_obj = dialogflow_v2.Intent()
        capture_success_intent_obj.display_name = (
            f"{capture_intent_obj.display_name}-success"
        )
        capture_success_intent_obj.events = [capture_success_intent_obj.display_name]
        capture_success_intent = Intent(capture_success_intent_obj)

        # capture failure node
        capture_failure_intent_obj = dialogflow_v2.Intent()
        capture_failure_intent_obj.display_name = (
            f"{capture_intent_obj.display_name}-failure"
        )
        capture_failure_intent_obj.events = [capture_failure_intent_obj.display_name]
        capture_failure_intent = Intent(capture_failure_intent_obj)

        intents = [capture_success_intent, capture_failure_intent]

        self.api.create_children(
            intents=intents, parent=capture_intent, language_code=language_code
        )

        # fallback node
        fallback_intent_obj = dialogflow_v2.Intent()
        fallback_intent_obj.display_name = f"{parent.display_name}-fallback"
        fallback_intent_obj.events = [fallback_intent_obj.display_name]
        fallback_intent_obj.action = f""
        fallback_intent_obj.messages = [
            dialogflow_v2.Intent.Message(payload={"local_entity_detection": ""})
        ]

        fallback_intent = Intent(fallback_intent_obj)
        fallback_intent = self.api.create_child(
            intent=fallback_intent, parent=parent, language_code=language_code
        )

        sent_config = {
            "api": self.api,
            "intent_names": [capture_failure_intent.display_name],
            "language_code": language_code,
        }
        sent_gen = SentimentGeneratorUnsafe(sent_config)
        sent_gen.run()

    def run(self, intent_names=None, language_code="en"):
        parent_names = intent_names if intent_names else self.config["intent_names"]

        for parent_name in parent_names:
            parent_name: str
            parent: Intent = self.api.intents["display_name"].get(parent_name)
            if not parent:
                print(f"Parent intent `{parent_name}` not found.")
                continue

            payload: dict = parent.custom_payload
            payload.update({"local_entity_detection": ""})
            parent.custom_payload = payload

            # create child updates parent
            # self.api.update_intent(intent=parent, language_code=language_code)

            self.create_entity_detector(parent, language_code)

            sleep(2)


if __name__ == "__main__":

    intent_names = ["haru-games"]

    base_dir = os.path.abspath(f"{os.path.dirname(__file__)}/../..")
    keys_dir = os.path.join(base_dir, ".temp/keys")

    config = {
        "credential": os.path.join(keys_dir, "haru-test.json"),
        "intent_names": intent_names,
        "language_code": "en",
    }

    gen = EntityDetectorGenerator(config)
    gen.run()
