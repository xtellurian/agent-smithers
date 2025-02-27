import os

import anthropic
from rich.console import Console
from rich.prompt import Prompt

from agent_smithers.env import ANTHROPIC_API_KEY
from agent_smithers.printer import print_assistant, print_system, print_user
from agent_smithers.tools import definitions, executor


class ChatSession:
    def __init__(self, api_key: str | None = None):
        self.api_key = (
            api_key or ANTHROPIC_API_KEY or os.environ.get("ANTHROPIC_API_KEY")
        )
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY must be provided either as an argument or environment variable"
            )
        self.client = anthropic.Client(api_key=self.api_key)
        self.console = Console()
        self.conversation = []

    def chat_loop(self):
        print_system("Starting chat with Agent Smithers (powered by Anthropic Claude)")
        print_system("Type 'exit' or 'quit' to end the conversation")

        while True:
            user_input = Prompt.ask("\n[bold green]You[/]")

            if user_input.lower() in ("exit", "quit"):
                print_system("Ending chat session")
                break

            print_user(user_input)

            try:
                # Create initial message
                messages = [
                    *[
                        {
                            "role": "user" if msg["role"] == "user" else "assistant",
                            "content": msg["content"],
                        }
                        for msg in self.conversation
                    ],
                    {"role": "user", "content": user_input},
                ]

                # Process tool calls until Claude no longer needs to use tools
                tool_calls_remain = True
                final_assistant_message = None

                while tool_calls_remain:
                    response = self.client.messages.create(
                        model="claude-3-opus-20240229",
                        max_tokens=1024,
                        messages=messages,
                        tools=definitions,
                    )

                    # Check if the response contains tool calls
                    has_tool_use = False
                    tool_results = []

                    for content in response.content:
                        if content.type == "tool_use":
                            has_tool_use = True
                            print_system(
                                f"Using tool: {content.name} with params {content.input}"
                            )
                            tool_response = executor(content)
                            print_system(f"Tool response: {tool_response}")

                            # Add tool result to send back
                            tool_results.append(
                                {
                                    "type": "tool_result",
                                    "tool_use_id": content.id,
                                    "content": str(tool_response),
                                }
                            )

                    if has_tool_use:
                        # Add the assistant's response and tool results to the message history
                        messages.append(
                            {"role": "assistant", "content": response.content}
                        )
                        messages.append({"role": "user", "content": tool_results})
                    else:
                        # No more tool calls, stop the loop
                        tool_calls_remain = False
                        final_assistant_message = response.content
                        break

                # Extract the text response after all tools have been used
                assistant_response = "".join(
                    [
                        content.text
                        for content in final_assistant_message
                        if content.type == "text"
                    ]
                )
                print_assistant(assistant_response)

                self.conversation.extend(
                    [
                        {"role": "user", "content": user_input},
                        {"role": "assistant", "content": assistant_response},
                    ]
                )

            except Exception as e:
                print_system(f"Error: {e!s}")


def start_chat_session(api_key: str | None = None):
    try:
        session = ChatSession(api_key)
        session.chat_loop()
    except ValueError as e:
        print_system(str(e))
