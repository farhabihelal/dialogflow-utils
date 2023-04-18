import os
import sys

sys.path.append(os.path.abspath(f"{os.path.dirname(__file__)}/../../dialogflow_utils"))
sys.path.append(
    os.path.abspath(
        f"{os.path.dirname(__file__)}/../../dialogflow_utils/dialogflow_api/src"
    )
)

import google.cloud.dialogflow_v2 as dialogflow_v2
from dialogflow import Dialogflow, Intent
from time import sleep
import json


def needs_fixing(intent: Intent) -> bool:
    payload: dict = intent.custom_payload
    if (
        "sentiment_classification_override" not in payload
        or not payload["sentiment_classification_override"]
    ):
        return True
    return False


def apply_fix(intent: Intent):
    payload: dict = intent.custom_payload

    payload["sentiment_classification_override"] = {
        "positive_intent": f"{intent.display_name}-positive",
        "neutral_limit": 0.5,
        "negative_intent": f"{intent.display_name}-negative",
        "neutral_intent": f"{intent.display_name}-neutral",
        "negative_limit": -0.5,
    }
    intent.custom_payload = payload


if __name__ == "__main__":
    parent_names = []

    base_dir = os.path.abspath(f"{os.path.dirname(__file__)}/../../")
    keys_dir = os.path.join(base_dir, ".temp/keys")

    config = {
        # "credential": os.path.join(keys_dir, "es.json"),
        "credential": os.path.join(keys_dir, "es2.json"),
        # "credential": os.path.join(keys_dir, "haru-test.json"),
        "language_code": "en",
    }
    df = Dialogflow(config)
    df.get_intents(language_code=config["language_code"])
    df.generate_tree()

    intents = []
    for intent_name, intent in df.intents["display_name"].items():
        intent_name: str
        intent: Intent

        if "dummy" in intent_name and "dummy-" not in intent_name:
            if needs_fixing(intent):
                apply_fix(intent)
                intents.append(intent)

    print("backing up... ", end="")
    df.create_version(
        "backup before fixing sentiment metadata of dummy intents from api.".title()
    )
    print("done")

    print("fixing... ", end="")
    df.batch_update_intents(
        intents=[x.intent_obj for x in intents], language_code=config["language_code"]
    )
    print("done")
