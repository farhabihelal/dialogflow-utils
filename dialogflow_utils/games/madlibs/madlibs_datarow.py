from dataclasses import dataclass, field
from dialogflow_payload_utils.src.dialogflow_payload_gen.do.base_rich_dataclass import (
    BaseRichDataClass,
)
import re


@dataclass
class MadlibDataRow(BaseRichDataClass):
    title: str = ""
    questions: list = field(default_factory=list)
    parameters: list = field(default_factory=list)
    madlib: str = ""

    def __post_init__(self):
        self.title = self.process_title(self.title)
        self.madlib = self.process_madlib(self.madlib)

    def process_title(self, title: str) -> str:
        title = title.lower().replace("-", " ").strip()
        title = re.sub("\s+", " ", title)
        title = title.replace(" ", "-")
        return title

    def process_madlib(self, madlib: str) -> str:
        for i, param in enumerate(self.parameters):
            param: str
            madlib = self.replace_parameter(madlib, param, i + 1)
        return madlib

    def replace_parameter(self, text: str, parameter: str, count: int) -> str:
        return text.replace(parameter, f"#globals.madlib_param_{count}")
