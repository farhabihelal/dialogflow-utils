# The purpose of this script is to add metadata to YesNo intents which are currently using Dialogflow for intent recognition.


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
    intent_obj: dialogflow_v2.Intent = intent.intent_obj
    intent_obj.action = "madlibs-outro"
    messages = []

    # for message in intent_obj.messages:
    #     message: dialogflow_v2.Intent.Message
    #     if message.text:
    #         pass

    intent_obj.messages = intent_obj.messages[:-1]

    return intent


def needs_fixing(intent: Intent) -> bool:
    return (
        "create-madlibs-" in intent.display_name
        and "fallback" not in intent.display_name
        and not intent.intent_obj.is_fallback
    )


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

    madlibs_root_intent_name = "madlibs"
    madlibs_root_intent = df.intents["display_name"][madlibs_root_intent_name]

    intents_to_fix = []
    for intent in madlibs_root_intent.all_children:
        intent: Intent

        if needs_fixing(intent):
            intent = fix(intent)
            intents_to_fix.append(intent)

    print("backing up... ", end="")
    df.create_version("backup before fixing old madlibs navigation from api.".title())
    print("done")

    print("fixing... ", end="")
    df.batch_update_intents(
        intents=[x.intent_obj for x in intents_to_fix],
        language_code=config["language_code"],
    )
    print("done")
