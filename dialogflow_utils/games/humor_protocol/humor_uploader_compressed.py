import sys
import os

sys.path.append(os.path.abspath(f"{os.path.dirname(__file__)}/.."))

import google.cloud.dialogflow_v2 as dialogflow_v2

from humor_uploader import HumorUploader, Intent


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
        root_intent_obj.priority = 0
        root_intent_obj.input_context_names = [
            self.api.sessions_client.context_path(
                self.api.project_id, "-", f"{root_intent_obj.display_name}"
            )
        ]
        root_intent_obj.parent_followup_intent_name = ""

        followup_context = dialogflow_v2.Context()
        followup_context.name = self.api.sessions_client.context_path(
            self.api.project_id, "-", f"{root_intent_obj.display_name}-followup"
        )
        followup_context.lifespan_count = 1
        followup_context.parameters = {}
        root_intent_obj.output_contexts = [followup_context]

        root_intent_obj: dialogflow_v2.Intent = self.api.create_intent(
            intent=root_intent_obj, language_code=language_code
        )
        root_intent = Intent(root_intent_obj)

        self.api.intents["name"][root_intent.name] = root_intent
        self.api.intents["display_name"][root_intent.display_name] = root_intent

        # create humor type intent and it's children
        for humor_type in humor_data:
            humor_type: str
            type_intent_obj = dialogflow_v2.Intent()
            type_intent_obj.parent_followup_intent_name = root_intent_obj.name
            type_intent_obj.display_name = (
                f"{self.process_intent_name(humor_type)}-compressed"
            )
            type_intent_obj.events = [type_intent_obj.display_name]
            type_intent_obj.priority = 0

            # type_intent_obj.input_context_names = [
            #     x.name for x in root_intent_obj.output_contexts
            # ]

            # followup_context = dialogflow_v2.Context()
            # followup_context.name = self.api.sessions_client.context_path(
            #     self.api.project_id, "-", f"{type_intent_obj.display_name}-followup"
            # )
            # followup_context.lifespan_count = 1
            # followup_context.parameters = None
            # type_intent_obj.output_contexts = [followup_context]

            # type_intent_obj: dialogflow_v2.Intent = self.api.create_intent(
            #     type_intent_obj, language_code=language_code
            # )

            type_intent = self.api.create_child(Intent(type_intent_obj), root_intent)

            humors_compressed = humor_data[humor_type]
            humor_intents = []
            for i, humor_compressed in enumerate(humors_compressed):
                humor_compressed: list
                humor_intent_obj = dialogflow_v2.Intent()
                # humor_intent_obj.parent_followup_intent_name = type_intent.name
                humor_intent_obj.display_name = f"{type_intent.display_name}-{i+1:03d}"
                # humor_intent_obj.input_context_names = [
                #     self.api.sessions_client.context_path(
                #         self.api.project_id, "-", type_intent_obj.display_name
                #     )
                # ]
                humor_intent_obj.events = [humor_intent_obj.display_name]
                humor_intent_obj.priority = 0
                humor_intent_obj.action = "humor-outro"

                # humor_intent_obj.input_context_names = [
                #     x.name for x in type_intent_obj.output_contexts
                # ]

                humor_intent_obj.messages = []
                msg = dialogflow_v2.Intent.Message()
                msg.text = dialogflow_v2.Intent.Message.Text(
                    text=[" ".join(x).strip() for x in humor_compressed]
                )
                humor_intent_obj.messages.append(msg)

                humor_intents.append(Intent(humor_intent_obj))

            # result = self.api.batch_update_intents(
            #     intents=humor_intent_objs, language_code=language_code
            # )

            self.api.create_children(
                intents=humor_intents, parent=type_intent, language_code=language_code
            )


if __name__ == "__main__":
    base_dir = os.path.abspath(f"{os.path.dirname(__file__)}/../..")
    keys_dir = os.path.join(base_dir, ".temp/keys")
    data_dir = os.path.join(base_dir, "data")

    config = {
        "db_path": os.path.join(data_dir, "Haru Humor Protocol.xlsx"),
        "credential": os.path.join(keys_dir, "haru-chat-games.json"),
        "language_code": "en",
    }

    uploader = HumorUploaderCompressed(config)
    uploader.run()
