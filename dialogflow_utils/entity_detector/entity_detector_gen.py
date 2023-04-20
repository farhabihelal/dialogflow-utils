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
        # fallback node
        fallback_nodes = [x for x in parent.children if x.intent_obj.is_fallback]
        fallback_intent: Intent = None

        if len(fallback_nodes) == 1:
            fallback_intent = fallback_nodes[0]

        elif len(fallback_nodes) > 1:
            raise ValueError(
                f"multiple fallback found for intent `{parent.display_name}`!".capitalize()
            )

        # capture node
        capture_intent_obj = dialogflow_v2.Intent()
        capture_intent_obj.display_name = f"{parent.display_name}-entity-capture"
        capture_intent_obj.events = [capture_intent_obj.display_name]
        capture_intent_obj.action = f"verify-entity"
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
        capture_success_intent_obj.messages = [
            dialogflow_v2.Intent.Message(payload={"node_type": "AnswerNode"})
        ]
        capture_success_intent = Intent(capture_success_intent_obj)

        # capture failure node
        capture_failure_intent_obj = dialogflow_v2.Intent()
        capture_failure_intent_obj.display_name = (
            f"{capture_intent_obj.display_name}-failure"
        )
        capture_failure_intent_obj.events = [capture_failure_intent_obj.display_name]
        capture_failure_intent_obj.messages = [
            dialogflow_v2.Intent.Message(payload={"node_type": "AnswerNode"})
        ]
        capture_failure_intent = Intent(capture_failure_intent_obj)

        intents = [capture_success_intent, capture_failure_intent]

        self.api.create_children(
            intents=intents, parent=capture_intent, language_code=language_code
        )

        # fallback node
        if not fallback_intent:
            fallback_intent_obj = dialogflow_v2.Intent()
            fallback_intent_obj.display_name = f"{parent.display_name}-fallback"
            fallback_intent_obj.events = [fallback_intent_obj.display_name]
            fallback_intent_obj.action = f""
            fallback_intent_obj.is_fallback = True
            fallback_intent_obj.messages = [
                dialogflow_v2.Intent.Message(
                    payload={"local_entity_detection": "", "node_type": "FallbackNode"}
                )
            ]

            fallback_intent = Intent(fallback_intent_obj)
            fallback_intent = self.api.create_child(
                intent=fallback_intent, parent=parent, language_code=language_code
            )

        sent_config = {
            "api": self.api,
            "intent_names": [fallback_intent.display_name],
            "language_code": language_code,
        }
        sent_gen = SentimentGeneratorUnsafe(sent_config)
        sent_gen.run()

    def run(self, intent_names=None, language_code="en"):
        parent_names = intent_names if intent_names else self.config["intent_names"]

        for i, parent_name in enumerate(parent_names):
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

            print(f"{parent_name}: success")
            if i + 1 < len(parent_names):
                sleep(10)


if __name__ == "__main__":
    intent_names = [
        # pet
        # "topic-pet-multiple-age",
        # "topic-pet-how-old-question",
        # lemurs
        # friends
        # "topic-day-four-friends-name"
        # travel
        # "topic-day-five-travel-last-place",
        # "topic-day-five-travel-favorite-food-not-collected",
        # "topic-day-five-favorite-continent-south-america",
        # "topic-day-five-favorite-continent-africa",
        # "topic-day-five-favorite-continent-asia",
        # olympics
        # "topic-olympics-handler-three",
        # "topic-olympics-would-compete-well-in-favorite-sport",
        # food
        "topic-day-three-food-summingup"
    ]

    base_dir = os.path.abspath(f"{os.path.dirname(__file__)}/../..")
    keys_dir = os.path.join(base_dir, ".temp/keys")

    config = {
        "credential": os.path.join(keys_dir, "es.json"),
        # "credential": os.path.join(keys_dir, "es2.json"),
        # "credential": os.path.join(keys_dir, "haru-test.json"),
        "intent_names": intent_names,
        "language_code": "en",
    }

    gen = EntityDetectorGenerator(config)
    day, session, topic = 3, 1, "food"
    print("backing up... ", end="")
    gen.api.create_version(
        f"backup before adding entity detections to day {day} session {session} {topic} topic.".title()
    )
    print("done")
    gen.run()
