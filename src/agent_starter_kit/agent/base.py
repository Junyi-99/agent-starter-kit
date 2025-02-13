import os
import socket
from datetime import datetime
from typing import Callable, Literal

from langfuse import Langfuse
from openai import OpenAI

AGENT_STARTER_KIT_VERSION = os.getenv("AGENT_STARTER_KIT_VERSION", "unknown")
AGENT_STARTER_KIT_RELEASE = os.getenv("AGENT_STARTER_KIT_RELEASE", "unknown")  # e.g. Nov 16, 2024 18:53

AGENT_STARTER_KIT_USER_ID = os.getenv("AGENT_STARTER_KIT_USER_ID", socket.gethostname())
AGENT_STARTER_KIT_SESSION_ID = os.getenv("AGENT_STARTER_KIT_SESSION_ID", "unspecified")  # Equal to the job-id of the backend


class Agent:
    """
    Every Agent has its own trace, which records all operations.
    """

    def __init__(self, name: str, temperature: float = 0.0, seed: int = 0, tags: list[str] | None = None, top_p: float = 0.1, tracing: bool = True):
        """
        @param name: Agent Name, e.g. "RuleApply" or "PaperScore"
        """
        self.name = name
        self.client = OpenAI()
        self.temperature = temperature  # OpenAI Temperature
        self.top_p = top_p  # OpenAI Top P
        self.seed = seed
        self.langfuse = Langfuse(
            secret_key=os.getenv("LANGFUSE_SECRET_KEY", "sk-lf-fdd5a88c-94d6-4640-a789-51f20b4a5067"),
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY", "pk-lf-576d14cc-4003-4cb0-812b-146e6dc059fd"),  # pd-org / development
            host=os.getenv("LANGFUSE_HOST", "https://pd-trace-3.xtra.science"),
        )
        self.tracing = tracing

        self.trace = self.langfuse.trace(
            name=self.name,
            tags=tags or [],
            user_id=AGENT_STARTER_KIT_USER_ID,
            session_id=AGENT_STARTER_KIT_SESSION_ID,
            version=AGENT_STARTER_KIT_VERSION,
            release=AGENT_STARTER_KIT_RELEASE,
            input="Please check the Observation for GENERATION",
            output="Please check the Observation for GENERATION",
            metadata={
                "hint": "Please check the Observation for GENERATION",
            },
        )

    def run(
        self,
        *,
        prompt: str | object,
        stream_callback: Callable[[str], None] | None = None,
        model: str = "gpt-4o-mini",
        response_format: Literal["text", "json_object"] = "text",
        tags: list[str] | None = None,
        metadata: dict | None = None,
        debug: bool = False,
    ) -> str:
        """
        Generate a response from the given prompt.
        @param prompt: It can be a string or a list of messages.
        @param stream_callback: A callback function that will be called with each new token in the response stream.
        @param model: The model to use for the generation. Default is "gpt-4o-mini"
        @param tags: Tags for the observation (not the trace).
        @param metadata: tracing only. you can put any key-value pairs in it.
        """
        trace_generate = self.trace.generation(
            name="generate_response",
            input=prompt,
            metadata={
                **(metadata or {}),
                "temperature": self.temperature,
                "top_p": self.top_p,
                "seed": self.seed,
            },
            tags=(tags or []),
            user_id=AGENT_STARTER_KIT_USER_ID,
            session_id=AGENT_STARTER_KIT_SESSION_ID,
            model=model,
            start_time=datetime.now(),
            level="DEBUG" if debug else "DEFAULT",
        )

        stream = self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}] if isinstance(prompt, str) else prompt,  # type: ignore
            model=model,
            temperature=self.temperature,
            top_p=self.top_p,
            seed=self.seed,
            response_format={"type": response_format},
            stream=True,
        )

        collected = []
        for s in stream:
            content = s.choices[0].delta.content
            if content is not None:
                collected.append(content)
                if stream_callback is not None:
                    stream_callback(content)
        output = "".join(collected)

        self.trace.update(output=output)  # update the trace with the final output
        trace_generate.update(output=output, end_time=datetime.now())
        return output
