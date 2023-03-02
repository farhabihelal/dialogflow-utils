import os
import sys

sys.path.append(os.path.abspath(f"{os.path.dirname(__file__)}/.."))

sys.path.append(os.path.abspath(f"{os.path.dirname(__file__)}/../.."))
from dialogflow_api.src.dialogflow import Dialogflow, Intent

import google.cloud.dialogflow_v2 as dialogflow_v2

from madlibs_datarow import MadlibDataRow
from madlibs_parser import MadlibsParser

from time import sleep


class MadlibsGenerator:
    def __init__(self, config: dict) -> None:
        self.configure(config)

        self.parser = MadlibsParser(config)

        self.api = Dialogflow(config)
        self.api.get_intents()
        self.api.generate_tree()

    def configure(self, config: dict):
        self.config = config

    def create_madlibs(self, madlib_data: list):
        for madlib in madlib_data:
            madlib: MadlibDataRow
            self.create_madlib(madlib)
            sleep(1)

    def create_madlib(self, madlib: MadlibDataRow, language_code="en"):
        root_intent_obj = (
            dialogflow_v2.Intent()
            if not self.api.intents["display_name"].get(madlib.title)
            else self.api.intents["display_name"][madlib.title].intent_obj
        )
        root_intent_obj.display_name = madlib.title
        root_intent_obj.events = [root_intent_obj.display_name]
        root_intent_obj.action = f"{root_intent_obj.display_name}-question-1"
        root_intent_obj.priority = 0

        # msg = dialogflow_v2.Intent.Message(
        #     text=dialogflow_v2.Intent.Message.Text(text=[madlib.questions[0]])
        # )
        # root_intent_obj.messages = [msg]

        root_intent_obj: dialogflow_v2.Intent = (
            self.api.create_intent(intent=root_intent_obj, language_code=language_code)
            if not self.api.intents["display_name"].get(root_intent_obj.display_name)
            else self.api.update_intent(
                intent=root_intent_obj, language_code=language_code
            )
        )
        root_intent = Intent(root_intent_obj)

        parent = root_intent
        for i in range(1, len(madlib.questions) + 1):
            intent_obj = dialogflow_v2.Intent()
            intent_obj.display_name = f"{root_intent_obj.display_name}-question-{i}"
            intent_obj.events = [intent_obj.display_name]
            intent_obj.parent_followup_intent_name = parent.name
            # intent_obj.action = (
            #     f"{root_intent_obj.display_name}-question-{i+1}"
            #     if i < len(madlib.questions)
            #     else f"{root_intent_obj.display_name}-madlib"
            # )
            if i > 1:
                training_phrase = dialogflow_v2.Intent.TrainingPhrase()
                part = dialogflow_v2.Intent.TrainingPhrase.Part()
                part.text = f"{madlib.parameters[i-2]}".replace("$", "").upper()
                part.entity_type = "@sys.any"
                training_phrase.parts = [part]
                intent_obj.training_phrases = [training_phrase]

                parameter = dialogflow_v2.Intent.Parameter()
                parameter.display_name = f"madlib_param_{i-1}"
                parameter.default_value = ""
                parameter.entity_type_display_name = "@sys.any"
                parameter.is_list = False
                parameter.mandatory = False
                parameter.value = f"${parameter.display_name}"

                intent_obj.parameters = [parameter]

            msg = dialogflow_v2.Intent.Message(
                text=dialogflow_v2.Intent.Message.Text(text=[madlib.questions[i - 1]])
            )
            intent_obj.messages = [msg]

            intent = Intent(intent_obj)
            self.api.create_child(
                intent=intent, parent=parent, language_code=language_code
            )
            parent = intent

        # final response
        response_intent_obj = dialogflow_v2.Intent()
        response_intent_obj.display_name = (
            f"{root_intent_obj.display_name}-final-response"
        )
        response_intent_obj.events = [response_intent_obj.display_name]
        response_intent_obj.action = f"{root_intent_obj.display_name}-madlib"

        training_phrase = dialogflow_v2.Intent.TrainingPhrase()
        part = dialogflow_v2.Intent.TrainingPhrase.Part()
        part.text = f"{madlib.parameters[-1]}".replace("$", "").upper()
        part.entity_type = "@sys.any"
        training_phrase.parts = [part]
        response_intent_obj.training_phrases = [training_phrase]

        parameter = dialogflow_v2.Intent.Parameter()
        parameter.display_name = f"madlib_param_{len(madlib.parameters)}"
        parameter.default_value = ""
        parameter.entity_type_display_name = "@sys.any"
        parameter.is_list = False
        parameter.mandatory = False
        parameter.value = f"${parameter.display_name}"

        response_intent_obj.parameters = [parameter]

        response_intent = Intent(response_intent_obj)
        self.api.create_child(
            intent=response_intent, parent=parent, language_code=language_code
        )

        # madlib
        madlib_intent_obj = dialogflow_v2.Intent()
        madlib_intent_obj.display_name = f"{root_intent_obj.display_name}-madlib"
        madlib_intent_obj.events = [madlib_intent_obj.display_name]
        madlib_intent_obj.action = "madlibs-outro"

        madlib_intent_obj.parameters = []
        for i in range(1, len(madlib.parameters) + 1):
            parameter = dialogflow_v2.Intent.Parameter()
            parameter.display_name = f"madlib_param_{i}"
            parameter.default_value = ""
            parameter.entity_type_display_name = "@sys.any"
            parameter.is_list = False
            parameter.mandatory = False
            parameter.value = f"#globals.{parameter.display_name}"
            madlib_intent_obj.parameters.append(parameter)

        msg = dialogflow_v2.Intent.Message(
            text=dialogflow_v2.Intent.Message.Text(text=[madlib.madlib])
        )
        madlib_intent_obj.messages = [msg]

        madlib_intent = Intent(madlib_intent_obj)
        self.api.create_child(
            intent=madlib_intent, parent=response_intent, language_code=language_code
        )

    def run(self, db_path: str = None, question_count: int = None):
        madlib_data: list = self.parser.run(
            db_path=db_path, question_count=question_count
        )
        # print(madlib_data)

        self.create_madlibs(madlib_data)


if __name__ == "__main__":
    base_dir = os.path.abspath(f"{os.path.dirname(__file__)}/../../..")
    keys_dir = os.path.join(base_dir, ".temp/keys")
    data_dir = os.path.join(base_dir, "data")

    config = {
        "db_path": os.path.join(data_dir, "Madlibs Scripts.xlsx"),
        "credential": os.path.join(keys_dir, "haru-chat-games.json"),
        "question_count": 3,
    }
    gen = MadlibsGenerator(config)
    gen.run()
