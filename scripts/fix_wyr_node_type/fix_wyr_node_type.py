# The purpose of this script is to fix node type of wyr intents which keeps getting changed by Dialog System.


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


def apply_fix(intent: Intent):
    payload: dict = intent.custom_payload
    payload["node_type"] = (
        "QuestionNode"
        if intent.display_name == "would-you-rather-tells-choices"
        else "QuestionNode"
        if intent.display_name == "would-you-rather-choices"
        else "AnswerNode"
    )
    intent.custom_payload = payload
    return intent


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

    wyr_root_intent_name = "would-you-rather-protocol"
    wyr_root_intent: Intent = df.intents["display_name"][wyr_root_intent_name]

    intents = []
    for intent in wyr_root_intent.all_children:
        intent: Intent
        intents.append(apply_fix(intent))

    print("backing up... ", end="")
    df.create_version("backup before fixing node type of wyr intents from api.".title())
    print("done")

    print("fixing... ", end="")
    df.batch_update_intents(
        intents=[x.intent_obj for x in intents], language_code=config["language_code"]
    )
    print("done")
