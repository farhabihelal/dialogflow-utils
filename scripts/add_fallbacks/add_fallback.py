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


def get_intent_data(parent_name: str) -> tuple:
    parent: Intent = df.intents["display_name"].get(parent_name)

    intent_obj = dialogflow_v2.Intent()
    intent_obj.display_name = f"{parent.display_name}-fallback"
    intent_obj.events = [intent_obj.display_name]
    intent_obj.action = ""
    intent_obj.messages = [
        dialogflow_v2.Intent.Message(
            payload={
                "node_type": "FallbackNode",
            }
        )
    ]
    intent_obj.is_fallback = True

    intent = Intent(intent_obj)

    return intent, parent


if __name__ == "__main__":
    parent_names = [
        "like-sports",
        "basketball-fact-question",
        "baseball-fact-question",
        "tennis-fact-question",
        "basketball-fact-yes",
        "baseball-fact-yes",
        "tennis-fact-yes",
        "likes-to-play-sports",
        "likes-to-watch-sports-or-fallback",
    ]

    base_dir = os.path.abspath(f"{os.path.dirname(__file__)}/../../")
    keys_dir = os.path.join(base_dir, ".temp/keys")

    config = {
        # "credential": os.path.join(keys_dir, "es.json"),
        "credential": os.path.join(keys_dir, "haru-test.json"),
        "language_code": "en",
    }
    df = Dialogflow(config)
    df.get_intents(language_code=config["language_code"])
    df.generate_tree()

    intents_data = [get_intent_data(x) for x in parent_names]

    for i, intent_data in enumerate(intents_data):
        intent_data: tuple
        intent, parent = intent_data
        df.create_child(
            intent=intent, parent=parent, language_code=config["language_code"]
        )

        print(f"{intent.display_name}: success")
        if i + 1 < len(intents_data):
            sleep(5)
