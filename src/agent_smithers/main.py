import argparse

from agent_smithers.console import start_chat_session


def main():
    parser = argparse.ArgumentParser(description="Agent Smithers CLI")
    parser.add_argument("--chat", action="store_true", help="Start a chat session")
    parser.add_argument("--api-key", type=str, help="Anthropic API key", default=None)

    args = parser.parse_args()

    if args.chat:
        start_chat_session(api_key=args.api_key)
    else:
        print("Use --chat to start a chat session")

if __name__ == "__main__":
    main()
