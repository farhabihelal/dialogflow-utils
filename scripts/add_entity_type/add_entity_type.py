import os
import sys

sys.path.append(os.path.abspath(f"{os.path.dirname(__file__)}/../../dialogflow_utils"))
sys.path.append(
    os.path.abspath(
        f"{os.path.dirname(__file__)}/../../dialogflow_utils/dialogflow_api/src"
    )
)

from db.xlsx import read_xlsx

from time import sleep
import json
import pandas as pd

import google.cloud.dialogflow_v2 as dialogflow_v2
from dialogflow import Dialogflow


def load_data(filepath: str) -> dict:
    data = read_xlsx(filepath)
    return data


def get_entity_types_data(data: dict) -> list:
    entity_types_data = {}
    for sheet_name, df in data.items():
        sheet_name: str
        df: pd.DataFrame

        entities = [str(x) if not pd.isna(x) else "" for x in df["entities"].tolist()]
        synonyms_data = [
            str(x) if not pd.isna(x) else "" for x in df["synonyms"].tolist()
        ]

        for i, (entity, synonyms) in enumerate(zip(entities, synonyms_data)):
            entity: str
            synonyms: str

            entity = entity.title()
            entities[i] = entity
            synonyms_data[i] = [x.strip() for x in synonyms.split(",") if x]
            synonyms_data[i].insert(0, entity)

        entity_type = dialogflow_v2.EntityType()
        entity_type.display_name = f"{sheet_name}"
        entity_type.entities = [
            {
                "value": entity,
                "synonyms": synonyms,
            }
            for entity, synonyms in zip(entities, synonyms_data)
        ]

        entity_types_data[entity_type.display_name] = entity_type

    return entity_types_data


if __name__ == "__main__":
    base_dir = os.path.abspath(f"{os.path.dirname(__file__)}/../../")
    keys_dir = os.path.join(base_dir, ".temp/keys")

    config = {
        "credential": os.path.join(keys_dir, "es.json"),
        # "credential": os.path.join(keys_dir, "es2.json"),
        # "credential": os.path.join(keys_dir, "haru-test.json"),
        "language_code": "en",
        "data_filepath": os.path.join(
            os.path.dirname(__file__), "entity-type-data.xlsx"
        ),
    }
    df = Dialogflow(config)

    entity_types = []
    entity_types_data = get_entity_types_data(data=load_data(config["data_filepath"]))

    print("Backing up...\t", end="")
    df.create_version("backup before adding entity types batch from api.".title())
    print("done")

    print("Adding...\t", end="")
    df.batch_update_entity_types(
        entity_types=entity_types, language_code=config["language_code"]
    )
    print("done")
