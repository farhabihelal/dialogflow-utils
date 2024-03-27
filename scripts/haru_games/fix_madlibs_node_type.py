# The purpose of this script is to fix intent metadata in api generated madlibs intents where Dialog System wrongly assigned node type for questions.


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
    custom_payload = dict(intent.custom_payload)
    custom_payload["node_type"] = "AnswerQuestionNode"
    intent.custom_payload = custom_payload
    return intent


def needs_fixing(intent: Intent) -> bool:
    return (
        any(x in intent.display_name for x in [f"question-{i+1}" for i in range(3)])
        and (
            "fallback" not in intent.display_name and not intent.intent_obj.is_fallback
        )
        and (
            "node_type" in intent.custom_payload
            and intent.custom_payload["node_type"] == "AnswerNode"
        )
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

    if not intents_to_fix:
        print("All good. No intents found to fix!")
        exit(0)

    print("backing up... ", end="")
    df.create_version(
        "backup before fixing node types in generated madlibs from api.".title()
    )
    print("done")

    print("fixing... ", end="")
    df.batch_update_intents(
        intents=[x.intent_obj for x in intents_to_fix],
        language_code=config["language_code"],
    )
    print("done")
