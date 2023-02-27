import sys
import os

sys.path.append(os.path.abspath(f"{os.path.dirname(__file__)}/.."))

import google.cloud.dialogflow_v2 as dialogflow_v2

from trivia_uploader import TriviaUploader


class TriviaUploaderCompressed(TriviaUploader):
    def __init__(self, config: dict) -> None:
        super().__init__(config)

    def load(self, db_path=None) -> dict:
        trivia_data = self.compress_trivia_data(super().load(db_path=db_path))
        self.trivia_data = trivia_data
        return trivia_data

    def compress_trivia_data(self, trivia_data: dict) -> dict:
        trivias_data_compressed = {}

        for trivia_type in trivia_data:
            trivias = trivia_data[trivia_type]
            trivias_compressed = [
                trivias[i : i + 30] for i in range(0, len(trivias), 30)
            ]
            trivias_data_compressed[trivia_type] = trivias_compressed

        return trivias_data_compressed

    def upload(self, trivia_data: dict = None, language_code: str = None):
        trivia_data = trivia_data if trivia_data else self.trivia_data
        language_code = language_code if language_code else self.config["language_code"]

        # create trivia root intent node
        root_intent_obj = dialogflow_v2.Intent()
        root_intent_obj.display_name = self.process_intent_name(
            "trivia-data-compressed"
        )
        root_intent_obj.events = [root_intent_obj.display_name]
        root_intent_obj.priority = -1

        root_intent_obj: dialogflow_v2.Intent = self.api.create_intent(
            intent=root_intent_obj, language_code=language_code
        )

        # create trivia type intent and it's children
        for trivia_type in trivia_data:
            trivia_type: str
            type_intent_obj = dialogflow_v2.Intent()
            type_intent_obj.parent_followup_intent_name = root_intent_obj.name
            type_intent_obj.display_name = (
                f"{self.process_intent_name(trivia_type)}-compressed"
            )
            type_intent_obj.events = [type_intent_obj.display_name]
            type_intent_obj.priority = -1

            type_intent_obj: dialogflow_v2.Intent = self.api.create_intent(
                type_intent_obj, language_code=language_code
            )

            trivias_compressed = trivia_data[trivia_type]
            trivia_intent_objs = []
            for i, trivia_compressed in enumerate(trivias_compressed):
                trivia_compressed: list
                trivia_intent_obj = dialogflow_v2.Intent()
                trivia_intent_obj.parent_followup_intent_name = type_intent_obj.name
                trivia_intent_obj.display_name = (
                    f"{type_intent_obj.display_name}-{i+1:03d}"
                )
                trivia_intent_obj.input_context_names = [
                    self.api.sessions_client.context_path(
                        self.api.project_id, "-", type_intent_obj.display_name
                    )
                ]
                trivia_intent_obj.events = [trivia_intent_obj.display_name]
                trivia_intent_obj.priority = -1

                trivia_intent_obj.messages = []
                msg = dialogflow_v2.Intent.Message()
                msg.text = dialogflow_v2.Intent.Message.Text(
                    text=[x for x in trivia_compressed]
                )
                trivia_intent_obj.messages.append(msg)

                trivia_intent_objs.append(trivia_intent_obj)

            result = self.api.batch_update_intents(
                intents=trivia_intent_objs, language_code=language_code
            )


if __name__ == "__main__":
    base_dir = os.path.abspath(f"{os.path.dirname(__file__)}/../..")
    keys_dir = os.path.join(base_dir, ".temp/keys")
    data_dir = os.path.join(base_dir, "data")

    config = {
        "db_path": os.path.join(data_dir, "Haru Trivia Protocol.xlsx"),
        "credential": os.path.join(keys_dir, "haru-test.json"),
        "language_code": "en",
    }

    uploader = TriviaUploaderCompressed(config)
    uploader.run()
