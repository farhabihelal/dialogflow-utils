if __name__ == "__main__":

    import os
    import sys

    sys.path.append(
        os.path.abspath(f"{os.path.dirname(__file__)}/../../dialogflow_utils")
    )
    sys.path.append(
        os.path.abspath(
            f"{os.path.dirname(__file__)}/../../dialogflow_utils/dialogflow_api/src"
        )
    )

    from dialogflow import Dialogflow

    from time import sleep

    intent_names = [
        "basketball-fact-yes",
        "baseball-fact-yes",
        "tennis-fact-yes",
        "knows-basketball-fact-no",
        "knew-baseball-fact-no",
        "knew-tennis-fact-no",
    ]

    base_dir = os.path.abspath(f"{os.path.dirname(__file__)}/../../")
    keys_dir = os.path.join(base_dir, ".temp/keys")

    config = {
        "credential": os.path.join(keys_dir, "es.json"),
        # "credential": os.path.join(keys_dir, "haru-test.json"),
    }
    df = Dialogflow(config)
    df.get_intents()
    df.generate_tree()

    for i, intent_name in enumerate(intent_names):
        intent_name: str
        intent_obj = df.intents["display_name"].get(intent_name)
        if not intent_obj:
            print(f"Error: {intent_name} not found!")
            continue
        df.convert_intent_type(
            intent=intent_obj, language_code="en", make_fallback=False
        )

        print(f"Success: {intent_name}")
        if i + 1 < len(intent_names):
            sleep(5)

    print("Done!")
