import sys
import os

sys.path.append(os.path.abspath(f"{os.path.dirname(__file__)}/.."))

import pandas as pd

from dialogflow_api.src.dialogflow import Dialogflow, Intent

import google.cloud.dialogflow_v2 as dialogflow_v2

from humor_uploader import HumorUploader


class HumorUploaderCompressed(HumorUploader):
    def __init__(self, config: dict) -> None:
        super().__init__(config)

    def load(self, db_path=None) -> dict:
        humor_data = self.compress_humor_data(super().load(db_path=db_path))
        self.humor_data = humor_data
        return humor_data

    def compress_humor_data(self, humor_data: dict) -> dict:
        humors_data_compressed = {}

        for humor_type in humor_data:
            humors = humor_data[humor_type]
            humors_compressed = [humors[i : i + 30] for i in range(0, len(humors), 30)]
            humors_data_compressed[humor_type] = humors_compressed

        return humors_data_compressed

    def upload(self, humor_data: dict = None, language_code: str = None):
        humor_data = humor_data if humor_data else self.humor_data
        language_code = language_code if language_code else self.config["language_code"]

        # create humor root intent node
        root_intent_obj = dialogflow_v2.Intent()
        root_intent_obj.display_name = self.process_intent_name("humor-data-compressed")
        root_intent_obj.events = [root_intent_obj.display_name]
        root_intent_obj.priority = -1

        root_intent_obj: dialogflow_v2.Intent = self.api.create_intent(
            intent=root_intent_obj, language_code=language_code
        )

        # create humor type intent and it's children
        for humor_type in humor_data:
            humor_type: str
            type_intent_obj = dialogflow_v2.Intent()
            type_intent_obj.parent_followup_intent_name = root_intent_obj.name
            type_intent_obj.display_name = (
                f"{self.process_intent_name(humor_type)}-compressed"
            )
            type_intent_obj.events = [type_intent_obj.display_name]
            type_intent_obj.priority = -1

            type_intent_obj: dialogflow_v2.Intent = self.api.create_intent(
                type_intent_obj, language_code=language_code
            )

            humors_compressed = humor_data[humor_type]
            humor_intent_objs = []
            for i, humor_compressed in enumerate(humors_compressed):
                humor_compressed: list
                humor_intent_obj = dialogflow_v2.Intent()
                humor_intent_obj.parent_followup_intent_name = type_intent_obj.name
                humor_intent_obj.display_name = (
                    f"{type_intent_obj.display_name}-{i+1:03d}"
                )
                humor_intent_obj.input_context_names = [
                    self.api.sessions_client.context_path(
                        self.api.project_id, "-", type_intent_obj.display_name
                    )
                ]
                humor_intent_obj.events = [humor_intent_obj.display_name]
                humor_intent_obj.priority = -1

                humor_intent_obj.messages = []
                msg = dialogflow_v2.Intent.Message()
                msg.text = dialogflow_v2.Intent.Message.Text(
                    text=[" ".join(x) for x in humor_compressed]
                )
                humor_intent_obj.messages.append(msg)

                humor_intent_objs.append(humor_intent_obj)

            result = self.api.batch_update_intents(
                intents=humor_intent_objs, language_code=language_code
            )


if __name__ == "__main__":
    base_dir = os.path.abspath(f"{os.path.dirname(__file__)}/../..")
    keys_dir = os.path.join(base_dir, ".temp/keys")
    data_dir = os.path.join(base_dir, "data")

    config = {
        "db_path": os.path.join(data_dir, "Haru Humor Protocol.xlsx"),
        "credential": os.path.join(keys_dir, "haru-test.json"),
        "language_code": "en",
    }

    uploader = HumorUploaderCompressed(config)
    uploader.run()
