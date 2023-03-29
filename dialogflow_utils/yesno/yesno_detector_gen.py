import os
import sys

sys.path.append(os.path.abspath(f"{os.path.dirname(__file__)}/.."))

from dialogflow_api.src.dialogflow import Dialogflow, Intent

import google.cloud.dialogflow_v2 as dialogflow_v2

from time import sleep

from sentiment.sentiment_gen_unsafe import SentimentGeneratorUnsafe


class YesNoDetectorGenerator:
    def __init__(self, config: dict) -> None:
        self.configure(config)

        self.api = self.config.get("api")
        if not self.api:
            self.api = Dialogflow(config)
            self.api.get_intents()
            self.api.generate_tree()

    def configure(self, config: dict):
        self.config = config

    def create_yesno_detector(self, parent: Intent, language_code: str = None):

        # fallback node
        fallback_nodes = [x for x in parent.children if x.intent_obj.is_fallback]
        fallback_intent: Intent = None

        if len(fallback_nodes) == 1:
            fallback_intent = fallback_nodes[0]

        # TODO: verify if multiple fallbacks are actually possible. Hunch is NO
        elif len(fallback_nodes) > 1:
            raise ValueError(
                f"multiple fallback found for intent `{parent.display_name}`!".capitalize()
            )

        # yes node
        yes_intent: Intent = self.api.intents["display_name"].get(
            f"{parent.display_name}-yes"
        )
        if not yes_intent:
            yes_intent_obj = dialogflow_v2.Intent()
            yes_intent_obj.display_name = f"{parent.display_name}-yes"
            yes_intent_obj.events = [yes_intent_obj.display_name]
            yes_intent_obj.messages = [
                dialogflow_v2.Intent.Message(
                    payload={
                        "node_type": "AnswerNode",
                        "local_classifier_class": "Yes",
                    }
                ),
                dialogflow_v2.Intent.Message(
                    text=dialogflow_v2.Intent.Message.Text(
                        text=["this is a yes response.".title()]
                    )
                ),
            ]
            yes_intent = Intent(yes_intent_obj)

        # no node
        no_intent: Intent = self.api.intents["display_name"].get(
            f"{parent.display_name}-no"
        )
        if not no_intent:
            no_intent_obj = dialogflow_v2.Intent()
            no_intent_obj.display_name = f"{parent.display_name}-no"
            no_intent_obj.events = [no_intent_obj.display_name]
            no_intent_obj.messages = [
                dialogflow_v2.Intent.Message(
                    payload={
                        "node_type": "AnswerNode",
                        "local_classifier_class": "No",
                    }
                ),
                dialogflow_v2.Intent.Message(
                    text=dialogflow_v2.Intent.Message.Text(
                        text=["this is a no response.".title()]
                    )
                ),
            ]
            no_intent = Intent(no_intent_obj)

        # fallback node
        if not fallback_intent:
            fallback_intent_obj = dialogflow_v2.Intent()
            fallback_intent_obj.display_name = f"{parent.display_name}-fallback"
            fallback_intent_obj.events = [fallback_intent_obj.display_name]
            fallback_intent_obj.messages = [
                dialogflow_v2.Intent.Message(
                    payload={
                        "local_classifier_class": "Fallback",
                        "node_type": "AnswerNode",
                    }
                ),
                dialogflow_v2.Intent.Message(
                    text=dialogflow_v2.Intent.Message.Text(
                        text=["this is a fallback response.".title()]
                    )
                ),
            ]
            fallback_intent = Intent(fallback_intent_obj)

        # create intents
        intents = [yes_intent, no_intent, fallback_intent]
        self.api.create_children(
            intents=intents, parent=parent, language_code=language_code
        )

        sleep(5)

        sent_config = {
            "api": self.api,
            "intent_names": [fallback_intent.display_name],
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

            # check parent node type
            parent_node_type: str = parent.custom_payload.get("node_type")

            if parent_node_type and parent_node_type not in [
                "QuestionNode",
                "AnswerQuestionNode",
            ]:
                raise ValueError(
                    f"`{parent.display_name}` has invalid node type. Expecting type `QuestionNode` but found `{parent_node_type}`"
                )

            payload: dict = parent.custom_payload
            payload.update(
                {
                    "node_type": "QuestionNode",
                    "local_intent_classifier": "YesNo",
                }
            )
            parent.custom_payload = payload

            # self.api.update_intent(intent=parent, language_code=language_code)

            self.create_yesno_detector(parent, language_code)

            sleep(2)


if __name__ == "__main__":

    intent_names = [
        # pet
        # "topic-pet-cat-followup",
        # "topic-pet-bird-followup",
        "topic-pet-hypothetical-pet-refresh-harder-cat",
        "topic-pet-hypothetical-pet-refresh-harder-dog",
        # lemurs
        "topic-lemurs-destination-merge",
        "topic-lemurs-are-from",
        "topic-lemurs-pet-collected",
        "topic-lemurs-fav-animal-collected",
        "topic-lemurs-no-animal-collected",
        "topic-lemurs-pet-collected-home-country-collected",
        "topic-lemurs-pet-collected-home-country-not-collected",
        "topic-lemurs-user-would-mind-no",
    ]

    base_dir = os.path.abspath(f"{os.path.dirname(__file__)}/../..")
    keys_dir = os.path.join(base_dir, ".temp/keys")

    config = {
        "credential": os.path.join(keys_dir, "es.json"),
        # "credential": os.path.join(keys_dir, "haru-test.json"),
        "intent_names": intent_names,
        "language_code": "en",
    }

    gen = YesNoDetectorGenerator(config)
    gen.run()
