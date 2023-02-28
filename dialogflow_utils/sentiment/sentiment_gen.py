import os
import sys

sys.path.append(os.path.abspath(f"{os.path.dirname(__file__)}/.."))

from dialogflow_api.src.dialogflow import Dialogflow, Intent

import google.cloud.dialogflow_v2 as dialogflow_v2

from time import sleep


class SentimentGenerator:
    def __init__(self, config: dict) -> None:
        self.configure(config)
        self.api = Dialogflow(config)
        self.api.get_intents()
        self.api.generate_tree()

        self.valid_sentiments = ["positive", "negative", "neutral"]
        pass

    def configure(self, config: dict):
        self.config = config

    def add_metadata(self, parent: Intent, sentiment_intents: dict):
        payload = parent.custom_payload
        metadata = {
            "sentiment_classification_override": {
                "positive_intent": f"{sentiment_intents['positive'].display_name}",
                "neutral_limit": 0.5,
                "neutral_intent": f"{sentiment_intents['neutral'].display_name}",
                "negative_limit": -0.5,
                "negative_intent": f"{sentiment_intents['negative'].display_name}",
            },
        }
        payload.update(metadata)
        parent.custom_payload = payload

        self.api.update_intent(
            intent=parent.intent_obj, language_code=self.config["language_code"]
        )

    def get_sentiment_intents(self, parent: Intent) -> dict:
        return {x: self.get_sentiment_intent(x, parent) for x in self.valid_sentiments}

    def get_sentiment_intent(self, sentiment: str, parent: Intent) -> Intent:
        sentiment = sentiment.lower()

        if sentiment not in self.valid_sentiments:
            raise ValueError(f"Invalid sentiment value: {sentiment}")

        intent_obj = dialogflow_v2.Intent()
        intent_obj.display_name = f"{parent.display_name}-{sentiment}"
        intent_obj.events = [intent_obj.display_name]
        intent_obj.messages.append(
            dialogflow_v2.Intent.Message(
                text=dialogflow_v2.Intent.Message.Text(
                    text=[f"this is {sentiment} sentiment path.".title()]
                )
            )
        )
        intent = Intent(intent_obj)
        return intent

    def run(self, intent_names=None, language_code="en"):
        parent_names = intent_names if intent_names else self.config["intent_names"]

        for parent_name in parent_names:
            parent_name: str
            parent: Intent = self.api.intents["display_name"][parent_name]
            sentiment_intents: dict = self.get_sentiment_intents(parent)

            self.add_metadata(parent, sentiment_intents)

            self.api.create_children(
                intents=list(sentiment_intents.values()),
                parent=parent,
                language_code=language_code,
            )
            sleep(0.5)


if __name__ == "__main__":

    intent_names = [
        "topic-name-react-feeling",
    ]

    base_dir = os.path.abspath(f"{os.path.dirname(__file__)}/../..")
    keys_dir = os.path.join(base_dir, ".temp/keys")

    config = {
        "credential": os.path.join(keys_dir, "haru-test.json"),
        "intent_names": intent_names,
        "language_code": "en",
    }

    gen = SentimentGenerator(config)
    gen.run()