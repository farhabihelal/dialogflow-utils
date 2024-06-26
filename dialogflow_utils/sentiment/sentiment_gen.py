import os
import sys

sys.path.append(os.path.abspath(f"{os.path.dirname(__file__)}/.."))

from dialogflow_api.src.dialogflow import Dialogflow, Intent

import google.cloud.dialogflow_v2 as dialogflow_v2

from time import sleep


class SentimentGenerator:
    def __init__(self, config: dict) -> None:
        self.configure(config)

        self.api = self.config.get("api")
        if not self.api:
            self.api = Dialogflow(config)
            self.api.get_intents()
            self.api.generate_tree()

        self.valid_sentiments = ["positive", "negative", "neutral"]

    def configure(self, config: dict):
        self.config = config

    def add_metadata(self, parent: Intent, sentiment_intents: dict) -> Intent:
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
        return parent

    def get_sentiment_intents(self, parent: Intent) -> dict:
        return {x: self.get_sentiment_intent(x, parent) for x in self.valid_sentiments}

    def get_sentiment_intent(self, sentiment: str, parent: Intent) -> Intent:
        sentiment = sentiment.lower()

        if sentiment not in self.valid_sentiments:
            raise ValueError(f"Invalid sentiment value: {sentiment}")

        intent_obj = dialogflow_v2.Intent()
        intent_obj.display_name = f"{parent.display_name}-{sentiment}"
        intent_obj.events = [intent_obj.display_name]
        intent_obj.action = self.get_action(parent)
        intent_obj.messages.append(
            dialogflow_v2.Intent.Message(payload={"node_type": "AnswerNode"})
        )
        intent_obj.messages.append(
            dialogflow_v2.Intent.Message(
                text=dialogflow_v2.Intent.Message.Text(
                    text=[f"this is {sentiment} sentiment path.".title()]
                )
            )
        )
        intent = Intent(intent_obj)
        return intent

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
            sentiment_intents: dict = self.get_sentiment_intents(parent)

            self.add_metadata(parent, sentiment_intents)

            self.api.create_children(
                intents=list(sentiment_intents.values()),
                parent=parent,
                language_code=language_code,
            )

            # remove action from parent
            parent.intent_obj.action = ""
            self.api.update_intent(
                intent=parent.intent_obj, language_code=language_code
            )

            print(f"{parent_name}: success")

            if i + 1 < len(parent_names):
                sleep(10)


if __name__ == "__main__":
    intent_names = [
        # "topic-day-three-food-summingup",
        # "topic-day-three-haru-food-merge"
        # friends
        # "topic-day-four-friend-like",
        # "topic-day-four-haru-is-friend-do",
        # "topic-day-four-good-friend",
        # "topic-day-four-friends-joke",
        # "topic-day-four-friends-joke-explain",
        # "topic-day-four-friends-user-tells-joke",
        # schools
        # "topic-day-four-school-user-fact"
        # music
        # "topic-music-genre-jazz-hum",
        # "topic-music-eyes-round",
        # "topic-music-chatbot-stand",
        # "topic-music-fav-dance-movie",
        # language
        # "topic-language-user-doesnot-want-to-learn-second-language",
        # "topic-language-call-for-user-only-speaks-english-fallback",
        # "topic-language-learn-english-at-school",
        # clothing
        # "topic-day-five-clothing-wearing-wool",
        # "topic-day-five-clothing-wearing-linen",
        # weather
        # "topic-day-five-weather-extreme-temperature",
        # travel
        # "topic-day-five-travel-enjoy-not",
        # "topic-day-five-travel-next-destination-collected",
        # "topic-day-five-travel-harus-favorite",
    ]

    base_dir = os.path.abspath(f"{os.path.dirname(__file__)}/../..")
    keys_dir = os.path.join(base_dir, ".temp/keys")

    config = {
        "api": None,
        # "credential": os.path.join(keys_dir, "es.json"),
        "credential": os.path.join(keys_dir, "es2.json"),
        # "credential": os.path.join(keys_dir, "haru-test.json"),
        "intent_names": intent_names,
        "language_code": "en",
    }

    gen = SentimentGenerator(config)

    day, session, topic = 5, 2, "travel"
    print("backing up... ", end="")
    gen.api.create_version(
        f"backup before adding safe sent paths to day {day} session {session} {topic} topic".title()
    )
    print("done")
    gen.run()
