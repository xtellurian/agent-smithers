from typing import Any

from anthropic import Anthropic
from anthropic.types import Message
from printer import print_assistant, print_system, print_user
from rich.console import Console
from rich.panel import Panel
from tools import definitions, executor


class Workflow:
    def __init__(self, client: Anthropic, model: str = "claude-3-5-sonnet-20241022"):
        self.client = client
        self.model = model
        self.messages: list[dict[str, Any]] = []
        self.console = Console()

    def send_message(self, content: str) -> None:
        self.messages.append({"role": "user", "content": content})
        print_user(content)

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=self.messages,
            tools=definitions,
        )

        self._handle_response(response)

        if response.stop_reason == "tool_use":
            tool_response = self._handle_tool_calls(response)
            if tool_response:
                self.messages.append(tool_response)
                # Get final response after tool use
                final_response = self.client.messages.create(
                    model=self.model,
                    max_tokens=1024,
                    messages=self.messages,
                    tools=definitions,
                )
                self._handle_response(final_response)

    def _handle_response(self, response: Message) -> None:
        message_content = {"role": response.role, "content": response.content}
        self.messages.append(message_content)

        for content in response.content:
            if content.type == "text":
                print_assistant(content.text)

    def _handle_tool_calls(self, response: Message) -> dict[str, Any] | None:
        for content in response.content:
            if content.type == "tool_use":
                tool_use_id = content.id
                print_system(f"Using tool: {content.name}")
                tool_response = executor(content)
                print_system(f"Tool response: {tool_response}")

                return {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": str(tool_response),
                        }
                    ],
                }
        return None

    def print_conversation(self) -> None:
        for message in self.messages:
            role = message["role"]
            content = message["content"]

            if isinstance(content, list):
                content = "\n".join(c.text for c in content if hasattr(c, "text"))
            if content:
                panel = Panel(
                    str(content),
                    title=role.upper(),
                    title_align="left",
                    border_style="blue" if role == "assistant" else "green",
                )
                self.console.print(panel)
