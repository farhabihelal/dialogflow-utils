import os
import sys

sys.path.append(os.path.abspath(f"{os.path.dirname(__file__)}/.."))

sys.path.append(os.path.abspath(f"{os.path.dirname(__file__)}/../.."))
from dialogflow_api.src.dialogflow import Dialogflow, Intent

import google.cloud.dialogflow_v2 as dialogflow_v2

import re


class HaruReactionsGenerator:
    def __init__(self, config: dict) -> None:
        self.configure(config)

        self.api = Dialogflow(config)
        self.api.get_intents()
        self.api.generate_tree()

    def configure(self, config: dict):
        self.config = config

    def create_haru_reactions(
        self, parent_intent_name: str = None, language_code: str = None
    ):
        parent = (
            self.api.intents["display_name"][parent_intent_name]
            if parent_intent_name
            else None
        )

        haru_reactions_root_intent_name = "haru-reactions"

        root_intent_obj = (
            dialogflow_v2.Intent()
            if not self.api.intents["display_name"].get(haru_reactions_root_intent_name)
            else self.api.intents["display_name"][
                haru_reactions_root_intent_name
            ].intent_obj
        )
        root_intent_obj.display_name = haru_reactions_root_intent_name
        root_intent_obj.events = [root_intent_obj.display_name]
        root_intent_obj.input_context_names = [
            self.api.sessions_client.context_path(
                self.api.project_id, "-", f"{root_intent_obj.display_name}"
            )
        ]
        root_intent_obj.priority = 0

        root_intent = Intent(root_intent_obj)

        if parent:
            root_intent = self.api.create_child(
                intent=root_intent, parent=parent, language_code=language_code
            )
            root_intent_obj = root_intent.intent_obj
        else:
            root_intent_obj: dialogflow_v2.Intent = (
                self.api.create_intent(
                    intent=root_intent_obj, language_code=language_code
                )
                if not self.api.intents["display_name"].get(
                    root_intent_obj.display_name
                )
                else self.api.update_intent(
                    intent=root_intent_obj, language_code=language_code
                )
            )
            root_intent._intent_obj = root_intent_obj

        intents = []

        # love playing
        love_playing_intent_obj = dialogflow_v2.Intent()
        love_playing_intent_obj.display_name = (
            f"{root_intent_obj.display_name}-love-playing"
        )
        love_playing_intent_obj.events = [love_playing_intent_obj.display_name]
        love_playing_intent_obj.parent_followup_intent_name = root_intent_obj.name
        love_playing_intent_obj.action = "continue-game"

        # Game name param
        love_playing_intent_obj.parameters = []
        parameter = dialogflow_v2.Intent.Parameter()
        parameter.display_name = f"game_name"
        parameter.default_value = ""
        parameter.entity_type_display_name = "@sys.any"
        parameter.is_list = False
        parameter.mandatory = False
        parameter.value = ""
        love_playing_intent_obj.parameters.append(parameter)

        love_playing_intent_obj.messages = []
        love_playing_intent_obj.messages.append(
            dialogflow_v2.Intent.Message(
                text=dialogflow_v2.Intent.Message.Text(
                    text=["Wow! You must really love $game_name!"]
                )
            )
        )

        intent = Intent(love_playing_intent_obj)
        intents.append(intent)

        # playing too much
        playing_too_much_intent_obj = dialogflow_v2.Intent()
        playing_too_much_intent_obj.display_name = (
            f"{root_intent_obj.display_name}-playing-too-much"
        )
        playing_too_much_intent_obj.events = [playing_too_much_intent_obj.display_name]
        playing_too_much_intent_obj.parent_followup_intent_name = root_intent_obj.name
        playing_too_much_intent_obj.action = "game-prompt-advanced-new-game"

        # Game name param
        playing_too_much_intent_obj.parameters = []
        parameter = dialogflow_v2.Intent.Parameter()
        parameter.display_name = f"game_name"
        parameter.default_value = ""
        parameter.entity_type_display_name = "@sys.any"
        parameter.is_list = False
        parameter.mandatory = False
        parameter.value = ""
        playing_too_much_intent_obj.parameters.append(parameter)

        playing_too_much_intent_obj.messages = []
        playing_too_much_intent_obj.messages.append(
            dialogflow_v2.Intent.Message(
                text=dialogflow_v2.Intent.Message.Text(text=["Hey!", "Wait."])
            )
        )
        playing_too_much_intent_obj.messages.append(
            dialogflow_v2.Intent.Message(
                text=dialogflow_v2.Intent.Message.Text(
                    text=["We have played $game_name enough already."]
                )
            )
        )
        playing_too_much_intent_obj.messages.append(
            dialogflow_v2.Intent.Message(
                text=dialogflow_v2.Intent.Message.Text(
                    text=[
                        "Let's try something else.",
                        "I want you to try something else.",
                    ]
                )
            ),
        )

        intent = Intent(playing_too_much_intent_obj)
        intents.append(intent)

        self.api.create_children(
            intents=intents, parent=root_intent, language_code=language_code
        )

    def run(
        self,
        # db_path: str = None,
        parent_intent_name: str = None,
        language_code: str = None,
    ):
        self.create_haru_reactions(
            parent_intent_name=parent_intent_name
            if parent_intent_name
            else self.config["parent_intent_name"],
            language_code=language_code
            if language_code
            else self.config["language_code"],
        )


if __name__ == "__main__":
    base_dir = os.path.abspath(f"{os.path.dirname(__file__)}/../../..")
    keys_dir = os.path.join(base_dir, ".temp/keys")
    data_dir = os.path.join(base_dir, "data")

    config = {
        # "db_path": os.path.join(data_dir, "would-you-rather-scripts.xlsx"),
        "credential": os.path.join(keys_dir, "haru-chat-games.json"),
        "parent_intent_name": "",
        "language_code": "en",
    }
    gen = HaruReactionsGenerator(config)
    gen.run()
