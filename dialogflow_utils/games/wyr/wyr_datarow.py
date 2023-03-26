from dataclasses import dataclass, field
from dialogflow_payload_utils.src.dialogflow_payload_gen.do.base_rich_dataclass import (
    BaseRichDataClass,
)


@dataclass
class WYRDataRow(BaseRichDataClass):
    choice: str = ""
    response: str = ""
