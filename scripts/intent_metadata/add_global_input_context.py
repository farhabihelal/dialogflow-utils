# The purpose of this script is to add global input contexts metadata to all global topic nodes.


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

import re


GLOBAL_TOPICS = []
EXCLUDED_TOPICS = ["topic-intro", "topic-intro-short", "topic-introduction-end"]


def is_global_topic(intent: Intent) -> bool:
    return (
        (intent.parent is None and intent.intent_obj.display_name.startswith("topic-"))
        or any(x in intent.intent_obj.display_name for x in GLOBAL_TOPICS)
        and not any(x in intent.intent_obj.display_name for x in EXCLUDED_TOPICS)
    )


def add_input_context(intent: Intent):
    payload = intent.custom_payload

    if not "input_contexts" in payload:
        payload["input_contexts"] = []
    payload["input_contexts"].append("global")
    payload["input_contexts"] = set(payload["input_contexts"])
    intent.custom_payload = payload

    return intent


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

        if is_global_topic(intent):
            intent = add_input_context(intent)
            intents.append(intent)

    print("backing up... ", end="")
    df.create_version("backup before adding global intent metadata from api.".title())
    print("done")

    print("adding... ", end="")
    df.batch_update_intents(
        intents=[x.intent_obj for x in intents], language_code=config["language_code"]
    )
    print("done")
