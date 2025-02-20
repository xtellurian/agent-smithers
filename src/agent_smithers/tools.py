from anthropic.types import ToolUseBlock

definitions = [
    {
        "name": "get_weather",
        "description": "Get the current weather in a given location",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city and state, e.g. San Francisco, CA",
                }
            },
            "required": ["location"],
        },
    }
]


def get_weather(*, location: str) -> str:
    return f"The weather in {location} is sunny."


def executor(block: ToolUseBlock):
    if block.name == "get_weather":
        return get_weather(**block.input)

    return None
