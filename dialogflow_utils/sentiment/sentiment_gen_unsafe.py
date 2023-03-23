import os
import sys

sys.path.append(os.path.abspath(f"{os.path.dirname(__file__)}/.."))

from dialogflow_api.src.dialogflow import Dialogflow, Intent

import google.cloud.dialogflow_v2 as dialogflow_v2

from time import sleep

from sentiment.sentiment_gen import SentimentGenerator


class SentimentGeneratorUnsafe(SentimentGenerator):
    def __init__(self, config: dict) -> None:
        super().__init__(config)

    def get_action(self, parent: Intent):
        action = ""

        if parent.intent_obj.action:
            action = parent.intent_obj.action

        elif len(parent.children) == 1:
            action = parent.children[0].intent_obj.action

        elif len(parent.children) > 1:
            for x in parent.children:
                x: Intent
                if x.intent_obj.is_fallback:
                    action = x.intent_obj.action

        return action

    def create_dummy(self, parent: Intent, language_code: str = None) -> Intent:
        dummy_intent_obj = dialogflow_v2.Intent()
        dummy_intent_obj.display_name = f"{parent.display_name}-dummy"
        dummy_intent_obj.events = [dummy_intent_obj.display_name]

        dummy_intent = Intent(dummy_intent_obj)
        dummy_intent = self.api.create_child(
            intent=dummy_intent, parent=parent, language_code=language_code
        )
        return dummy_intent

    def run(self, intent_names=None, language_code="en", refresh=True):
        if refresh:
            self.api.get_intents()
            self.api.generate_tree()

        parent_names = intent_names if intent_names else self.config["intent_names"]

        for parent_name in parent_names:
            parent_name: str
            parent: Intent = self.api.intents["display_name"].get(parent_name)
            if not parent:
                print(f"Parent intent `{parent_name}` not found.")
                continue

            payload: dict = parent.custom_payload
            payload.update({"sentiment_classification_override": {}})
            parent.custom_payload = payload

            # create child updates parent
            # self.api.update_intent(intent=parent, language_code=language_code)

            dummy_intent: Intent = self.create_dummy(parent)
            sentiment_intents: dict = self.get_sentiment_intents(dummy_intent)
            self.add_metadata(dummy_intent, sentiment_intents)

            self.api.create_children(
                intents=list(sentiment_intents.values()),
                parent=dummy_intent,
                language_code=language_code,
            )

            # remove action from parent
            if parent.intent_obj.action:
                parent.intent_obj.action = ""
                self.api.update_intent(
                    intent=parent.intent_obj, language_code=language_code
                )
            sleep(2)


if __name__ == "__main__":

    intent_names = ["haru-games"]

    base_dir = os.path.abspath(f"{os.path.dirname(__file__)}/../..")
    keys_dir = os.path.join(base_dir, ".temp/keys")

    config = {
        "api": None,
        "credential": os.path.join(keys_dir, "haru-test.json"),
        "intent_names": intent_names,
        "language_code": "en",
    }

    gen = SentimentGenerator(config)
    gen.run()
