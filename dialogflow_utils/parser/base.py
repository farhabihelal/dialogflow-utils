class BaseParser:
    def __init__(self, config: dict) -> None:
        self.configure(config)
        pass

    def configure(self, config: dict):
        self.config = config
