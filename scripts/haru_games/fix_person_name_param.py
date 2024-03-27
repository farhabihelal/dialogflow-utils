# The purpose of this script is to fix `person_name` parameter use in the game script. This param is not collected in the Demo.


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


def fix(intent: Intent) -> Intent:
    return intent


def needs_fixing(intent: Intent) -> bool:
    return any(["person_name" in y for x in intent.text_messages for y in x])


if __name__ == "__main__":
    parent_names = []

    base_dir = os.path.abspath(f"{os.path.dirname(__file__)}/../../")
    keys_dir = os.path.join(base_dir, ".temp/keys")

    config = {
        # "credential": os.path.join(keys_dir, "es.json"),
        # "credential": os.path.join(keys_dir, "es2.json"),
        # "credential": os.path.join(keys_dir, "haru-test.json"),
        "credential": os.path.join(keys_dir, "haru-chat-games.json"),
        "language_code": "en",
    }
    df = Dialogflow(config)
    df.get_intents(language_code=config["language_code"])
    df.generate_tree()

    intents_to_fix = []
    for intent_name, intent in df.intents["display_name"].items():
        intent_name: str
        intent: Intent

        if needs_fixing(intent):
            intent = fix(intent)
            intents_to_fix.append(intent)

    if not intents_to_fix:
        print("All good. No intents found to fix!")
        exit(0)

    print("backing up... ", end="")
    df.create_version("backup before fixing person_name param from api.".title())
    print("done")

    print("fixing... ", end="")
    df.batch_update_intents(
        intents=[x.intent_obj for x in intents_to_fix],
        language_code=config["language_code"],
    )
    print("done")
