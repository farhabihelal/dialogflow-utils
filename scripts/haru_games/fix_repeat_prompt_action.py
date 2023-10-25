# The purpose of this script is to fix nodes that have `prompt-repeat-game` action.


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


def needs_fixing(intent: Intent) -> bool:
    return intent.intent_obj.action == "prompt-repeat-game"


def apply_fix(intent: Intent):
    intent.intent_obj.action = "repeat-prompt"
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

    intents = []
    for intent in df.intents["display_name"].values():
        intent: Intent
        if needs_fixing(intent):
            intents.append(apply_fix(intent))

    if not intents:
        print("All good. No intents found to fix!")
        exit(0)

    print("backing up... ", end="")
    df.create_version(
        "backup before fixing nodes with `prompt-repeat-game` action from api.".title()
    )
    print("done")

    print("fixing... ", end="")
    df.batch_update_intents(
        intents=[x.intent_obj for x in intents], language_code=config["language_code"]
    )
    print("done")
