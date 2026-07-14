from dataclasses import dataclass


@dataclass(frozen=True)
class AgentConfig:
    name: str
    instructions: str
    max_steps: int = 5


config = AgentConfig("repo-helper", "Inspect before editing.", 4)
print(f"agent={config.name} max_steps={config.max_steps} has_run={hasattr(config, 'run')}")
