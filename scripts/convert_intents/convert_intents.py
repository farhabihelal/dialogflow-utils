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

    from dialogflow import Dialogflow, Intent

    from time import sleep

    intent_names = ["topic-day-three-haru-meal-time-fallback"]

    base_dir = os.path.abspath(f"{os.path.dirname(__file__)}/../../")
    keys_dir = os.path.join(base_dir, ".temp/keys")

    config = {
        # "credential": os.path.join(keys_dir, "es.json"),
        "credential": os.path.join(keys_dir, "haru-test.json"),
    }
    df = Dialogflow(config)
    df.get_intents()
    df.generate_tree()

    for i, intent_name in enumerate(intent_names):
        intent_name: str
        intent: Intent = df.intents["display_name"].get(intent_name)
        if not intent:
            print(f"Error: {intent_name} not found!")
            continue

        payload = intent.custom_payload
        payload["node_type"] = "FallbackNode"
        intent.custom_payload = payload
        df.convert_intent_type(intent=intent, language_code="en", make_fallback=True)

        print(f"Success: {intent_name}")
        if i + 1 < len(intent_names):
            sleep(5)

    print("Done!")
