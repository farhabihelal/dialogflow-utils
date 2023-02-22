from google.cloud.dialogflow_v2 import Intent


# def get_duplicate(api, source_intent_name: str, target_intent_name: str):

#     source_intent = api.intents["display_name"][source_intent_name]
#     target_intent = api.intents["display_name"][target_intent_name]

#     target_intent.intent_obj.training_phrases = list(
#         source_intent.intent_obj.training_phrases
#     )
#     target_intent.intent_obj.parameters = list(source_intent.intent_obj.parameters)

#     # reset name
#     for x in target_intent.intent_obj.training_phrases:
#         x: Intent.TrainingPhrase
#         x.name = ""

#     # reset name
#     for x in target_intent.intent_obj.parameters:
#         x: Intent.Parameter
#         x.name = ""

#     return target_intent


def get_duplicate(source_intent_obj: Intent, target_intent_obj: Intent) -> Intent:

    target_intent_obj.training_phrases = list(source_intent_obj.training_phrases)
    target_intent_obj.parameters = list(source_intent_obj.parameters)

    # reset name
    for x in target_intent_obj.training_phrases:
        x: Intent.TrainingPhrase
        x.name = ""

    # reset name
    for x in target_intent_obj.parameters:
        x: Intent.Parameter
        x.name = ""

    return target_intent_obj


def get_duplicate_batch(data: list) -> list:
    dup_targets_all = []

    for item in data:
        source = item["source"]
        targets = item["targets"]
        dup_targets = [get_duplicate(source, x) for x in targets]
        dup_targets_all.extend(dup_targets)

    return dup_targets_all


def duplicate(api, data: list):
    intent_data = []

    for item in data:
        source = item["source"]
        targets = item["targets"]

        intent_data_item = {
            "source": api.intents["display_name"][source].intent_obj,
            "targets": [api.intents["display_name"][x].intent_obj for x in targets],
        }
        intent_data.append(intent_data_item)

    dup_intents = get_duplicate_batch(intent_data)
    api.batch_update_intents(dup_intents)


if __name__ == "__main__":
    import sys
    import os

    base_dir = os.path.abspath(f"{os.path.dirname(__file__)}/../..")
    df_path = os.path.join(base_dir, "dialogflow_utils/dialogflow_api/src")
    keys_dir = os.path.join(base_dir, ".temp/keys")

    sys.path.append(df_path)

    from dialogflow import Dialogflow

    config = {
        "credential": os.path.join(keys_dir, "haru-chat-games.json"),
    }

    api = Dialogflow(config)
    api.get_intents()
    api.generate_tree()

    # source_intent_name = "haruscope-does-not-know-sign"
    # target_intent_name = "test-intent"

    # dup_target = get_duplicate(api, source_intent_name, target_intent_name)
    # api.update_intent(dup_target.intent_obj)

    data = [
        {
            "source": "haruscope-does-not-know-sign",
            "targets": ["test-intent"],
        }
    ]

    duplicate(api, data)
