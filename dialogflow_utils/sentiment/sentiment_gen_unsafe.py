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
        # intro
        # "topic-intro-engage-smalltalk-must-fallback",
        # "topic-intro-name-double-check-fallback",
        # age
        # "topic-day-one-session-one-age-again-fallback",
        # "topic-day-one-session-one-age-fallback",
        # "topic-day-one-session-one-age-parents-fallback"
        # "topic-day-one-session-one-age-grandparents-fallback",
        # "topic-day-one-session-one-age-parents-job-sarcastic-handle-fallback",
        # names origins
        # "topic-day-one-session-one-names-origins-meaning-fallback",
        # "topic-day-one-session-one-names-origins-meaning-haru-fallback",
        # "topic-day-one-session-one-names-happy-with-name-fallback",
        # "topic-day-one-session-one-remembering-names-fallback",
        # "topic-day-one-session-one-haru-name-fallback",
        # "topic-day-one-session-one-last-name-fallback",
        # "topic-day-one-session-one-confirm-last-name-fallback",
        # "topic-day-one-session-one-family-name-capture-again-fallback",
        # "topic-day-one-session-one-family-name-double-check-fallback",
        # "topic-day-one-session-one-collect-name-origin-fallback",
        # "topic-day-one-session-one-haru-origin-fallback",
        # "topic-day-one-session-one-ever-been-fallback",
        # "topic-day-one-session-one-collect-name-origin-sarcastic-handle-fallback",
        # "topic-day-one-session-one-collect-name-origin-confirm-fallback",
        # "topic-day-one-session-one-haru-origin-sarcastic-handle-fallback",
        # hometown
        # "topic-hometown-fallback",
        # "topic-hometown-still-live-there-fallback",
        # "topic-hometown-still-live-there-no-fallback",
        # "topic-hometown-unknown-type-of-building",
        # "topic-hometown-looking-for-a-new-roommate-fallback",
        # "topic-hometown-new-roommate-yes-reaction",
        # "topic-hometown-looking-for-a-new-roommate-no-reaction",
        # "topic-hometown-not-from-homecountry-capture-birthcountry",
        # "topic-hometown-homecountry-live-now-fallback",
        # "topic-hometown-what-question-fallback",
        # travel homecountry
        # "topic-travel-homecountry-human-guesses-harus-from-non-japan-country",
        # "topic-travel-homecountry-human-from-other-country",
        # "topic-travel-homecountry-human-unsure-about-haru-visiting",
        # "topic-travel-homecountry-favorite-hemisphere-any-answer",
        # "topic-travel-homecountry-human-been-to-sweden-fallback",
        # "topic-travel-homecountry-human-seen-the-northern-lights-fallback",
        # "topic-travel-homecountry-wants-to-know-where-the-lights-come-from",
        # "topic-travel-homecountry-loves-how-humans-interact-with-nature",
        # family
        # "topic-day-two-family-siblings-not-captured-not-oldest-fallback",
        # "topic-day-two-family-siblings-oldest-fallback",
        # sports
        # "like-sports-fallback",
        # "basketball-fact-question-fallback",
        # "baseball-fact-question-fallback",
        # "tennis-fact-question-fallback",
        # "basketball-fact-yes-fallback",
        # "baseball-fact-yes-fallback",
        # "tennis-fact-yes-fallback",
        # "likes-to-play-sports-fallback",
        # "likes-to-watch-sports-or-fallback-fallback",
        # "coach-reaction-fallback",
        # "more-sports-facts-question-fallback",
        # "play-or-watch-sports-question-fallback",
        # "play-professionally-fallback",
        # hobbies
        # "topic-day-three-hobbies-fallback",
        # "topic-day-three-hobbies-fun-fallback",
        # "topic-day-three-hobbies-video-games-fallback",
        # "topic-day-three-hobbies-no-video-games-fallback",
        # "topic-day-three-hobbies-suggest-video-game-fact-fallback",
        # "topic-day-three-hobbies-video-game-fact-fallback",
        # "topic-day-three-hobbies-haru-fallback",
        # "topic-day-three-hobbies-riddle-fallback",
        # "topic-day-three-hobbies-chess-fact-fallback",
        # "topic-day-three-hobbies-wrappingup-fallback",
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
