class BaseLLM:
    def generate(self, messages, tools=None):
        raise NotImplementedError("Subclasses must implement generate().")
