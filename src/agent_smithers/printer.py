from rich.console import Console

console = Console()


def print_assistant(message: str):
    console.print(f"🤖 [bold blue]{message}[/]")


def print_user(message: str):
    console.print(f"👤 [bold green]{message}[/]")


def print_system(message: str):
    console.print(f"⚙️ [bold red]{message}[/]")
