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


def get_intent_data(intent_def: dict) -> tuple:
    parent = df.intents["display_name"].get(intent_def["parent_name"])

    intent_obj = dialogflow_v2.Intent()
    intent_obj.display_name = intent_def["display_name"]
    intent_obj.events = [intent_obj.display_name]
    intent_obj.action = intent_def["action"]

    intent_obj.messages = []
    for message_type in intent_def["messages"]:
        if message_type == "payload":
            intent_obj.messages.append(
                dialogflow_v2.Intent.Message(payload=intent_def["messages"]["payload"])
            )
        elif message_type == "text":
            for text_messages in intent_def["messages"]["text"]:
                text_messages: list
                intent_obj.messages.append(
                    dialogflow_v2.Intent.Message(
                        text=dialogflow_v2.Intent.Message.Text(text=text_messages)
                    )
                )
    intent_obj.is_fallback = intent_def["is_fallback"]

    intent = Intent(intent_obj)

    return intent, parent


if __name__ == "__main__":
    base_dir = os.path.abspath(f"{os.path.dirname(__file__)}/../../")
    keys_dir = os.path.join(base_dir, ".temp/keys")

    config = {
        # "credential": os.path.join(keys_dir, "es.json"),
        "credential": os.path.join(keys_dir, "haru-test.json"),
        "language_code": "en",
        "intents_definitions": os.path.join(
            os.path.dirname(__file__), "intents_def.json"
        ),
    }
    df = Dialogflow(config)
    df.get_intents(language_code=config["language_code"])
    df.generate_tree()

    intents_data = []
    with open(config["intents_definitions"]) as f:
        intents_def = json.load(f)
        intents_data = [get_intent_data(x) for x in intents_def["intents"]]

    for i, intent_data in enumerate(intents_data):
        intent_data: tuple
        intent, parent = intent_data
        df.create_child(
            intent=intent, parent=parent, language_code=config["language_code"]
        )

        print(f"{intent.display_name}: success")
        if i + 1 < len(intents_data):
            sleep(5)
