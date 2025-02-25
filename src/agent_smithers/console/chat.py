import os
from typing import Optional

import anthropic
from rich.console import Console
from rich.prompt import Prompt

from agent_smithers.env import ANTHROPIC_API_KEY
from agent_smithers.printer import print_assistant, print_system, print_user


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
                response = self.client.messages.create(
                    model="claude-3-opus-20240229",
                    max_tokens=1024,
                    messages=[
                        *[
                            {
                                "role": "user"
                                if msg["role"] == "user"
                                else "assistant",
                                "content": msg["content"],
                            }
                            for msg in self.conversation
                        ],
                        {"role": "user", "content": user_input},
                    ],
                )

                assistant_response = response.content[0].text
                print_assistant(assistant_response)

                self.conversation.extend(
                    [
                        {"role": "user", "content": user_input},
                        {"role": "assistant", "content": assistant_response},
                    ]
                )

            except Exception as e:
                print_system(f"Error: {str(e)}")


def start_chat_session(api_key: Optional[str] = None):
    try:
        session = ChatSession(api_key)
        session.chat_loop()
    except ValueError as e:
        print_system(str(e))
