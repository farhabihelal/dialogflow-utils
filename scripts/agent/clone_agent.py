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
    base_dir = os.path.abspath(f"{os.path.dirname(__file__)}/../../")
    keys_dir = os.path.join(base_dir, ".temp/keys")

    config = {
        "src_credential": os.path.join(keys_dir, "es.json"),
        # "src_credential": os.path.join(keys_dir, "es2.json"),
        # "src_credential": os.path.join(keys_dir, "child-in-hospital.json"),
        # "src_credential": os.path.join(keys_dir, "haru-test.json"),
        # "dst_credential": os.path.join(keys_dir, "es.json"),
        # "dst_credential": os.path.join(keys_dir, "es2.json"),
        # "dst_credential": os.path.join(keys_dir, "child-in-hospital.json"),
        "dst_credential": os.path.join(keys_dir, "haru-test.json"),
        "language_code": "en",
    }

    src_config = {
        "credential": config["src_credential"],
        "language_code": config["language_code"],
    }
    df_src = Dialogflow(src_config)
    # df_src.get_intents(language_code=config["language_code"])

    dst_config = {
        "credential": config["dst_credential"],
        "language_code": config["language_code"],
    }
    df_dst = Dialogflow(dst_config)

    src_agent_name = os.path.splitext(os.path.basename(src_config["credential"]))[
        0
    ].title()
    dst_agent_name = os.path.splitext(os.path.basename(dst_config["credential"]))[
        0
    ].title()

    print(f"Backing up {dst_agent_name}...\t", end="")
    df_dst.create_version(f"Backup before cloning `{src_agent_name}` from api.".title())
    print("done")

    print("Cloning...\t", end="")
    response = df_src.export_agent()
    df_dst.restore_agent(response)
    print("done")

    print("Training agent...\t", end="")
    operation = df_dst.train_agent()
    operation.result()
    print("done")
