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


def is_yesno(intent: Intent) -> bool:
    if len(intent.children) < 3:
        return False

    found_yes = found_no = found_fallback = False

    for x in intent.children:
        x: Intent
        if "command-" in x.display_name:
            continue
        if "yes" in x.display_name and "yes-" not in x.display_name:
            found_yes = True
        elif "no" in x.display_name and "no-" not in x.display_name:
            found_no = True
        elif (
            x.is_fallback
            and "fallback" in x.display_name
            and "fallback-" not in x.display_name
        ):
            found_fallback = True

    return found_yes and found_no and found_fallback


def get_yesno_data(intent: Intent) -> dict:
    yesno_data = {"parent": intent}

    for x in intent.children:
        x: Intent
        if "yes" in x.display_name and "yes-" not in x.display_name:
            yesno_data["yes"] = x
        elif "no" in x.display_name and "no-" not in x.display_name:
            yesno_data["no"] = x
        elif (
            x.is_fallback
            and "fallback" in x.display_name
            and "fallback-" not in x.display_name
        ):
            yesno_data["fallback"] = x

    return yesno_data


def needs_fixing(yesno_data: dict) -> bool:
    for key, intent in yesno_data.items():
        key: str
        intent: Intent

        payload: dict = intent.custom_payload
        if key == "parent":
            if (
                "local_intent_classifier" not in payload
                or payload["local_intent_classifier"] != "YesNo"
            ):
                return True
        elif key in ["yes", "no", "fallback"]:
            if (
                "local_classifier_class" not in payload
                or payload["local_classifier_class"] != key.capitalize()
            ):
                return True

        return False


def apply_fix(yesno_data: dict):
    for key, intent in yesno_data.items():
        key: str
        intent: Intent

        payload: dict = intent.custom_payload
        if key == "parent":
            payload["local_intent_classifier"] = "YesNo"

        elif key in ["yes", "no", "fallback"]:
            payload["local_classifier_class"] = key.capitalize()

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

        if is_yesno(intent):
            yesno_data = get_yesno_data(intent)
            if needs_fixing(yesno_data):
                apply_fix(yesno_data)
                intents.extend(list(yesno_data.values()))

    print("backing up... ", end="")
    df.create_version(
        "backup before fixing metadata of yes no fallback intents from api.".title()
    )
    print("done")

    print("fixing... ", end="")
    df.batch_update_intents(
        intents=[x.intent_obj for x in intents], language_code=config["language_code"]
    )
    print("done")
