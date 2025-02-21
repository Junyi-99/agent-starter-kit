class AgentPromptMgr:
    """

    Example:

    ```
    from agent_start_kit.agent.prompt import AgentPromptMgr

    with AgentPromptMgr(__file__, category="eval") as prompt:
        prompt = prompt.replace(name="John", age="20")
    ```

    """

    def __init__(self, file_path: str, category: str | None = None):
        if category is not None:
            self.file_path = file_path[:-3] + f".{category}.prompt"
        else:
            self.file_path = file_path[:-3] + ".prompt"
        self.content = None

    def __enter__(self):
        with open(self.file_path, "r") as fp:
            self.content = fp.read()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def replace(self, **kwargs) -> str:
        """
        Replace the placeholder in prompt file with the given values.

        The key must be the placeholder name and the value must be the value to replace with.
        This function will replace the text enclosed in curly braces with the given value.

        Example:

        ```
        prompt.replace(name="John", age="20")
        ```

        "You are a {name} and you are {age} years old." will be replaced with "You are a John and you are 20 years old."
        """
        if self.content is None:
            raise ValueError("Content is not loaded. Use 'with' statement to load the content.")

        for key, value in kwargs.items():
            self.content = self.content.replace("{%s}" % (key,), value)

        return self.content
