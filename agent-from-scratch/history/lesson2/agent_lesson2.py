class Agent:
    def __init__(self, llm, instructions, tools):
        self.llm = llm
        self.instructions = instructions
        self.tools = tools
