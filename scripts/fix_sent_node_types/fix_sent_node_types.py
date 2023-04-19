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


def needs_fixing(intent: Intent):
    payload: dict = intent.custom_payload

    if "node_type" not in payload or payload["node_type"] != "AnswerNode":
        return True
    return False


def apply_fix(intent: Intent):
    payload: dict = intent.custom_payload
    payload["node_type"] = "AnswerNode"
    intent.custom_payload = payload


if __name__ == "__main__":
    parent_names = []

    base_dir = os.path.abspath(f"{os.path.dirname(__file__)}/../../")
    keys_dir = os.path.join(base_dir, ".temp/keys")

    config = {
        # "credential": os.path.join(keys_dir, "es.json"),
        # "credential": os.path.join(keys_dir, "es2.json"),
        "credential": os.path.join(keys_dir, "haru-test.json"),
        "language_code": "en",
    }
    df = Dialogflow(config)
    df.get_intents(language_code=config["language_code"])
    df.generate_tree()

    intents = []
    for intent_name, intent in df.intents["display_name"].items():
        intent_name: str
        intent: Intent

        if any([x in intent.display_name for x in ["positive", "negative", "neutral"]]):
            if needs_fixing(intent):
                apply_fix(intent)
                intents.append(intent)

    print("backing up... ", end="")
    df.create_version(
        "backup before fixing node type of sentiment intents from api.".title()
    )
    print("done")

    print("fixing... ", end="")
    df.batch_update_intents(
        intents=[x.intent_obj for x in intents], language_code=config["language_code"]
    )
    print("done")
