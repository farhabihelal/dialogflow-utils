import sys
import os

sys.path.append(os.path.abspath(f"{os.path.dirname(__file__)}/.."))

import google.cloud.dialogflow_v2 as dialogflow_v2

from trivia_uploader import TriviaUploader, Intent

import pandas as pd


class TriviaByCountryUploader(TriviaUploader):
    def __init__(self, config: dict) -> None:
        super().__init__(config)

        self.node_prefix = "trivia-by-country-"

    def process_trivias(self, db: dict = None) -> dict:
        db = db if db else self.db

        trivia_data = {}

        for sheet in db:
            df: pd.DataFrame = db[sheet]
            countries = [
                str(x) if not pd.isna(x) else "" for x in df["Country"].tolist()
            ]
            trivias = [str(x) if not pd.isna(x) else "" for x in df["Trivia"].tolist()]
            alt_trivia_list = [
                [str(x) if not pd.isna(x) else "" for x in df[f"Alt {i}"].tolist()]
                for i in range(1, 4)
            ]

            trivia_data = {}
            for i, (country, trivia) in enumerate(zip(countries, trivias)):
                country: str
                trivia: str

                if not trivia_data.get(country):
                    trivia_data[country] = []

                trivia_data[country].append(trivia)
                trivia_data[country].extend(
                    [alt_trivia_list[x][i] for x in range(3) if alt_trivia_list[x][i]]
                )

        return trivia_data

    def upload(self, trivia_data: dict = None, language_code: str = None):
        trivia_data = trivia_data if trivia_data else self.trivia_data
        language_code = language_code if language_code else self.config["language_code"]

        # root intent
        if not self.api.intents["display_name"].get(
            self.process_intent_name("trivia-by-country")
        ):
            # create trivia root intent node
            root_intent_obj = dialogflow_v2.Intent()
            root_intent_obj.display_name = self.process_intent_name("trivia-by-country")
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

            # root_intent_obj: dialogflow_v2.Intent = self.api.create_intent(
            #     intent=root_intent_obj, language_code=language_code
            # )
            root_intent = Intent(root_intent_obj)

            self.api.intents["name"][root_intent.name] = root_intent
            self.api.intents["display_name"][root_intent.display_name] = root_intent

        else:
            # use existing root intent
            root_intent = self.api.intents["display_name"][
                self.process_intent_name("trivia-by-country")
            ]

        trivia_intents = []

        # create trivia type intent and it's children
        for country, trivias in trivia_data.items():
            country: str
            trivias: list

            country_intent_obj = dialogflow_v2.Intent()
            country_intent_obj.parent_followup_intent_name = root_intent.name
            country_intent_obj.display_name = (
                f"trivia-country-{self.process_intent_name(country)}"
            )
            country_intent_obj.events = [country_intent_obj.display_name]
            country_intent_obj.priority = 0
            country_intent_obj.action = "trivia-by-country-outro"

            country_intent_obj.messages = []
            msg = dialogflow_v2.Intent.Message()
            msg.text = dialogflow_v2.Intent.Message.Text(
                text=[x.strip() for x in trivias]
            )
            country_intent_obj.messages.append(msg)

            trivia_intents.append(Intent(intent_obj=country_intent_obj))

        self.api.create_children(
            intents=trivia_intents,
            parent=root_intent,
            language_code=language_code,
        )

    def upload(self, trivia_data: dict = None, language_code: str = None):
        trivia_data = trivia_data if trivia_data else self.trivia_data
        language_code = language_code if language_code else self.config["language_code"]

        # root intent
        if not self.api.intents["display_name"].get(
            self.process_intent_name(f"{self.node_prefix}")
        ):
            # create root intent
            root_intent = self.get_root_node()

            root_intent = Intent(
                self.api.create_intent(
                    intent=root_intent.intent_obj, language_code=language_code
                )
            )

            self.api.intents["name"][root_intent.name] = root_intent
            self.api.intents["display_name"][root_intent.display_name] = root_intent

        else:
            # use existing root intent
            root_intent = self.api.intents["display_name"][
                self.process_intent_name(f"{self.node_prefix}")
            ]

        intro_node = self.get_intro_node()
        outro_node = self.get_outro_node()
        prompt_node = self.get_prompt_node()
        data_node = self.get_data_node()

        self.api.create_children(
            intents=[intro_node, outro_node, prompt_node, data_node],
            parent=root_intent,
            language_code=language_code,
        )

    def get_root_node(self) -> Intent:
        intent_obj = dialogflow_v2.Intent()
        intent_obj.display_name = f"{self.node_prefix}"
        intent_obj.events = [intent_obj.display_name]
        intent_obj.action = ""
        intent_obj.priority = 0
        intent_obj.input_context_names = [
            self.api.sessions_client.context_path(
                self.api.project_id, "-", f"{intent_obj.display_name}"
            )
        ]

        return Intent(intent_obj)

    def get_intro_node(self) -> Intent:
        intent_obj = dialogflow_v2.Intent()
        intent_obj.display_name = f"{self.node_prefix}-intro"
        intent_obj.events = [intent_obj.display_name]
        intent_obj.action = ""
        intent_obj.priority = 0

        return Intent(intent_obj)

    def get_outro_node(self) -> Intent:
        intent_obj = dialogflow_v2.Intent()
        intent_obj.display_name = f"{self.node_prefix}-outro"
        intent_obj.events = [intent_obj.display_name]
        intent_obj.action = ""
        intent_obj.priority = 0

        return Intent(intent_obj)

    def get_prompt_node(self) -> Intent:
        intent_obj = dialogflow_v2.Intent()
        intent_obj.display_name = f"{self.node_prefix}-prompt"
        intent_obj.events = [intent_obj.display_name]
        intent_obj.action = ""
        intent_obj.priority = 0

        return Intent(intent_obj)

    def get_data_node(self) -> Intent:
        intent_obj = dialogflow_v2.Intent()
        intent_obj.display_name = f"{self.node_prefix}-data"
        intent_obj.events = [intent_obj.display_name]
        intent_obj.action = ""
        intent_obj.priority = 0

        return Intent(intent_obj)


if __name__ == "__main__":
    base_dir = os.path.abspath(f"{os.path.dirname(__file__)}/../../..")
    keys_dir = os.path.join(base_dir, ".temp/keys")
    data_dir = os.path.join(base_dir, "data")

    config = {
        "db_path": os.path.join(data_dir, "Haru Trivia Protocol.xlsx"),
        "credential": os.path.join(keys_dir, "haru-chat-games.json"),
        "language_code": "en",
    }

    uploader = TriviaByCountryUploader(config)
    uploader.run()
