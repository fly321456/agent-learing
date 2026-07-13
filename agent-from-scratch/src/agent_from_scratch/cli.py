import argparse
from dataclasses import replace
from pathlib import Path
import sys

from .agent import Agent
from .config import RuntimeConfig
from .llm import OpenAILLM
from .runner import RetryPolicy, Runner
from .session import CheckpointStore, ContextWindow, Session, SessionStore
from .tools import ToolContext, ToolSpec, create_default_tools
from .tracing import JsonlTraceWriter


DEFAULT_INSTRUCTIONS = """You are a careful coding agent working inside one workspace.
Inspect before editing. Use the smallest relevant tool. Never claim a command or edit
succeeded unless the tool result confirms it. Summarize changes and verification."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the course Coding Agent.")
    parser.add_argument("prompt", nargs="?", help="Task for the agent")
    parser.add_argument("--resume", metavar="RUN_ID", help="Resume a saved checkpoint")
    parser.add_argument("--workspace", type=Path, help="Workspace boundary")
    parser.add_argument("--model", help="OpenAI model; defaults to OPENAI_MODEL")
    parser.add_argument("--max-steps", type=int, help="Maximum model turns for this invocation")
    parser.add_argument("--session", help="Persist conversational messages under this ID")
    parser.add_argument("--trace", type=Path, help="Write runtime events as JSONL")
    return parser


def _approve(tool: ToolSpec, arguments: dict) -> bool:
    print(f"Approval required: {tool.name} {arguments}", file=sys.stderr)
    return input("Allow this operation? [y/N] ").strip().lower() in {"y", "yes"}


def _display_event(event) -> None:
    if event.type == "tool_called":
        print(f"[{event.step}] tool -> {event.data['name']}", file=sys.stderr)
    elif event.type == "tool_completed":
        print(
            f"[{event.step}] tool <- {event.data['name']} ({event.data['status']})",
            file=sys.stderr,
        )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if bool(args.prompt) == bool(args.resume):
        parser.error("provide either a prompt or --resume")

    config = RuntimeConfig.from_env()
    if args.workspace:
        config = replace(config, workspace=args.workspace.resolve())
    if args.model:
        config = replace(config, model=args.model)
    if args.max_steps:
        config = replace(config, max_steps=args.max_steps)
    if not config.model:
        parser.error("provide --model or set OPENAI_MODEL")

    agent = Agent(
        name="coding-agent",
        instructions=DEFAULT_INSTRUCTIONS,
        llm=OpenAILLM(model=config.model),
        tools=create_default_tools(),
        max_steps=config.max_steps,
    )
    checkpoint_store = CheckpointStore(config.workspace / ".agent" / "checkpoints")
    runner = Runner(
        retry_policy=RetryPolicy(attempts=config.retry_attempts),
        checkpoint_store=checkpoint_store,
    )
    context = ToolContext(
        workspace=config.workspace,
        approval=_approve,
        command_timeout=config.command_timeout,
    )
    trace_writer = JsonlTraceWriter(args.trace) if args.trace else None

    def event_sink(event) -> None:
        _display_event(event)
        if trace_writer:
            trace_writer(event)

    if args.resume:
        result = runner.resume(agent, args.resume, context=context, event_sink=event_sink)
    else:
        history: list[dict[str, str]] = []
        session = None
        session_store = None
        if args.session:
            session_store = SessionStore(config.workspace / ".agent" / "sessions")
            session_path = session_store.directory / f"{args.session}.json"
            session = session_store.load(args.session) if session_path.exists() else Session(args.session)
            history = ContextWindow(config.context_chars).trim(session.messages)
        result = runner.run(
            agent,
            args.prompt,
            context=context,
            event_sink=event_sink,
            history=history,
        )
        if session is not None and session_store is not None:
            session.append("user", args.prompt)
            if result.content:
                session.append("assistant", result.content)
            session_store.save(session)

    if result.content:
        print(result.content)
    else:
        print(f"Run ended: {result.finish_reason}", file=sys.stderr)
    return 0 if result.finish_reason == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
