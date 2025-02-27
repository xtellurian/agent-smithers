from rich.console import Console

console = Console()


def print_assistant(message: str):
    console.print(f"🤖 [bold blue]{message}[/]")


def print_user(message: str):
    console.print(f"👤 [bold green]{message}[/]")


def print_system(message: str):
    # ensure this is only 1 line
    short_message = message.split("\n")[0][:400] + ("..." if len(message) > 400 else "")
    console.print(f"⚙️ [bold red]{short_message}[/]")
