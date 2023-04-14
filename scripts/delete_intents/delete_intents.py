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


if __name__ == "__main__":
    intent_names = [
        # "topic-pet-favorite-fallback-dummy",
        # "topic-pet-hypothetical-pet-refresh-fallback",
        "topic-lemurs-pet-collected-home-country-not-collected-not-native-dummy",
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

    for i, intent_name in enumerate(intent_names):
        intent_name: str
        df.delete_subtree(intent_name)

        print(f"{intent_name}: success")
        if i + 1 < len(intent_names):
            sleep(5)
