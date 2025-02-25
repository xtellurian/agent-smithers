from anthropic import Anthropic
from env import ANTHROPIC_API_KEY
from workflow import Workflow

client = Anthropic(api_key=ANTHROPIC_API_KEY)


def do_something():
    workflow = Workflow(client)
    workflow.send_message("Simulate Celery worker latency with 10 workers")
    workflow.print_conversation()
