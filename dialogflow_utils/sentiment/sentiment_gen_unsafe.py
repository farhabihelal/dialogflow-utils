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

        if parent.action:
            action = parent.action

        elif len(parent.children) == 1:
            action = parent.children[0].action

        elif len(parent.children) > 1:
            for x in parent.children:
                x: Intent
                if x.intent_obj.is_fallback:
                    action = x.action

        return action

    def create_dummy(self, parent: Intent, language_code: str = None) -> Intent:
        dummy_intent_obj = dialogflow_v2.Intent()
        dummy_intent_obj.display_name = f"{parent.display_name}-dummy"
        dummy_intent_obj.events = [dummy_intent_obj.display_name]
        # dummy_intent_obj.priority = -1

        dummy_intent_obj.messages = [
            dialogflow_v2.Intent.Message(payload={"node_type": "DisabledNode"})
        ]

        dummy_intent = Intent(dummy_intent_obj)

        parent.action = dummy_intent_obj.display_name
        dummy_intent = self.api.create_child(
            intent=dummy_intent, parent=parent, language_code=language_code
        )
        return dummy_intent

    def run(self, intent_names=None, language_code="en", refresh=True):
        if refresh:
            self.api.get_intents()
            self.api.generate_tree()

        parent_names = intent_names if intent_names else self.config["intent_names"]

        for i, parent_name in enumerate(parent_names):
            parent_name: str
            parent: Intent = self.api.intents["display_name"].get(parent_name)
            if not parent:
                print(f"Parent intent `{parent_name}` not found.")
                continue

            payload: dict = parent.custom_payload
            payload.update({"sentiment_classification_override": {}})
            parent.custom_payload = payload

            dummy_intent: Intent = self.create_dummy(parent)
            sentiment_intents_data: dict = self.get_sentiment_intents(dummy_intent)
            self.add_metadata(dummy_intent, sentiment_intents_data)
            self.apply_sent_map(sentiment_intents_data)

            # update parent metadata
            parent.action = dummy_intent.display_name
            parent._intent_obj = self.api.update_intent(
                intent=parent.intent_obj, language_code=language_code
            )

            self.api.create_children(
                intents=list(sentiment_intents_data.values()),
                parent=dummy_intent,
                language_code=language_code,
            )

            print(f"{parent_name}: success")

            if i + 1 < len(parent_names):
                sleep(10)

    def apply_sent_map(self, sentiment_intents_data):
        if not self.config.get("sent_map"):
            return

        if hasattr(sentiment_intents_data, "positive"):
            sentiment_intents_data[
                "positive"
            ].action = f"{self.config['sent_map']['positive']}"
        if hasattr(sentiment_intents_data, "neutral"):
            sentiment_intents_data[
                "neutral"
            ].action = f"{self.config['sent_map']['neutral']}"
        if hasattr(sentiment_intents_data, "negative"):
            sentiment_intents_data[
                "negative"
            ].action = f"{self.config['sent_map']['negative']}"


if __name__ == "__main__":
    intent_names = [
        # "topic-day-three-food-fallback",
        # "topic-day-three-haru-food-know-fallback",
        # "topic-day-three-haru-food-donot-know-fallback",
        # "topic-day-three-haru-food-guess",
        # "topic-day-three-haru-food-guess-fallback",
        # "topic-day-three-haru-yesterday-fallback",
        # "topic-day-three-favorite-food-collected-fallback",
        # "topic-day-three-favorite-food-collected-where-fallback",
        # "topic-day-three-favorite-food-nooldes-china-explain-fallback",
        # "topic-day-three-favorite-food-burgers-america-explain-fallback",
        # "topic-day-three-favorite-food-pizza-italy-explain-fallback",
        # "topic-day-three-favorite-food-nooldes-where-fallback",
        # friends
        # "topic-day-four-friends-fallback",
        # "topic-day-four-haru-is-friend-fallback",
        # "topic-day-four-friend-visited-fallback",
        # "topic-day-four-friends-make-laugh-fallback",
        # "topic-day-four-friends-user-joke-fallback",
    ]

    base_dir = os.path.abspath(f"{os.path.dirname(__file__)}/../..")
    keys_dir = os.path.join(base_dir, ".temp/keys")

    config = {
        "api": None,
        # "credential": os.path.join(keys_dir, "es.json"),
        "credential": os.path.join(keys_dir, "haru-test.json"),
        "intent_names": intent_names,
        "language_code": "en",
    }

    gen = SentimentGeneratorUnsafe(config)
    gen.run()
