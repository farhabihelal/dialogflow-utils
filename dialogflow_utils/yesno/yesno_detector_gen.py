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
        create_sentiments = False
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
        # check sent paths are already available in fallback
        if not self.has_unsafe_sentiments(fallback_intent):
            create_sentiments = True

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
            create_sentiments = True
            fallback_intent_obj = dialogflow_v2.Intent()
            fallback_intent_obj.display_name = f"{parent.display_name}-fallback"
            fallback_intent_obj.events = [fallback_intent_obj.display_name]
            fallback_intent_obj.messages = [
                dialogflow_v2.Intent.Message(
                    payload={
                        "local_classifier_class": "Fallback",
                        "node_type": "FallbackNode",
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

        if create_sentiments:
            sent_config = {
                "api": self.api,
                "intent_names": [fallback_intent.display_name],
                "language_code": language_code,
                "sent_map": {
                    "positive": yes_intent.display_name,
                    "neutral": yes_intent.display_name,
                    "negative": no_intent.display_name,
                },
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

            # check parent node type
            parent_node_type: str = parent.custom_payload.get("node_type")

            if parent_node_type and parent_node_type not in [
                "QuestionNode",
                "AnswerQuestionNode",
            ]:
                raise ValueError(
                    f"`{parent.display_name}` has invalid node type. Expecting type [`QuestionNode`, `AnswerQuestionNode`] but found `{parent_node_type}`"
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

            print(f"{parent_name}: success")
            if i + 1 < len(parent_names):
                sleep(10)

    def has_unsafe_sentiments(self, intent: Intent) -> bool:
        """Checks whether an intent has unsafe sentiment paths.
        The logic is very simple. It checks whether a dummy intent is present with 3 children.

        Args:
            intent (Intent)

        Returns:
            bool
        """
        if len(intent.children) == 0:
            return False
        elif (
            len(intent.children) == 1 and "dummy" not in intent.children[0].display_name
        ):
            return False
        else:
            for x in intent.children:
                x: Intent
                if "dummy" in x.display_name:
                    return True if len(x.children) == 3 else False
        return False


if __name__ == "__main__":
    intent_names = [
        # family
        # "topic-day-two-family-siblings-not-captured-not-oldest",
        # pet
        # "topic-pet-cat-followup",
        # "topic-pet-bird-followup",
        # "topic-pet-hypothetical-pet-refresh-harder-cat",
        # "topic-pet-hypothetical-pet-refresh-harder-dog",
        # lemurs
        # "topic-lemurs-destination-merge",
        # "topic-lemurs-are-from",
        # "topic-lemurs-pet-collected",
        # "topic-lemurs-fav-animal-collected",
        # "topic-lemurs-no-animal-collected",
        # "topic-lemurs-pet-collected-home-country-collected",
        # "topic-lemurs-pet-collected-home-country-not-collected",
        # "topic-lemurs-user-would-mind-no",
        # birthday
        # "topic-birthday-age-collected",
        # "topic-birthday-age-not-collected",
        # "topic-birthday-handle-one",
        # "topic-birthday-celebrating",
        # "topic-birthday-handle-two",
        # "topic-birthday-sibling-not-collected",
        # "topic-birthday-handle-two-wanted",
        # "topic-birthday-giving-gifts",
        # "topic-birthday-sibling-collected",
        # "topic-birthday-gifts",
        # "topic-birthday-gifts-handle-four",
        # "topic-birthday-perfect-gift",
        # # food
        # "topic-day-three-haru-more-food",
        # "topic-day-three-haru-meal-time",
        # "topic-day-three-favorite-food-nooldes-china-explain",
        # "topic-day-three-favorite-food-pizza-italy-explain",
        # "topic-day-three-favorite-food-burgers-america-explain",
        # sports
        # "topic-sports",
        # "coach-question",
        # hobbies
        # "topic-day-three-hobbies",
        # "topic-day-three-hobbies-gaming",
        # "topic-day-three-hobbies-no-video-games",
        # "topic-day-three-hobbies-chess-fact",
        # "topic-day-three-hobbies-chess-fact-say",
        # "topic-day-three-hobbies-video-game-fact",
        # "topic-day-three-hobbies-wrappingup",
    ]

    base_dir = os.path.abspath(f"{os.path.dirname(__file__)}/../..")
    keys_dir = os.path.join(base_dir, ".temp/keys")

    config = {
        # "credential": os.path.join(keys_dir, "es.json"),
        "credential": os.path.join(keys_dir, "haru-test.json"),
        "intent_names": intent_names,
        "language_code": "en",
    }

    gen = YesNoDetectorGenerator(config)
    gen.run()
