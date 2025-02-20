from anthropic import Anthropic
from env import ANTHROPIC_API_KEY

print(ANTHROPIC_API_KEY)
client = Anthropic(api_key=ANTHROPIC_API_KEY)


def do_something():
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[{"role": "user", "content": "Hello, Claude"}],
    )
    print(message.content)
