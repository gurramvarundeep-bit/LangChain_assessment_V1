from pydantic import BaseModel
from typing import Literal
from langchain_core.runnables import RunnableConfig


class AgentConfig(BaseModel):
    max_iterations: int = 3
    max_searches_per_iteration: int = 5
    model: str = "gpt-4o"
    temperature: float = 0.1
    report_style: str = "detailed"
    search_provider: Literal["tavily", "exa", "serpapi"] = "tavily"
    streaming: bool = False

    def to_configurable(self) -> dict:
        return self.model_dump()


def get_config(config: RunnableConfig | None = None) -> AgentConfig:
    if config and config.get("configurable"):
        return AgentConfig(**config["configurable"])
    return AgentConfig()