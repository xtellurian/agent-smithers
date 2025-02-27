import base64
import datetime
from io import BytesIO
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import matplotlib.pyplot as plt
from anthropic.types import ToolUseBlock

from agent_smithers import env
from agent_smithers.github.client import GitHubClient, GitHubClientConfig
from agent_smithers.latency_modelling.example import (
    WorkerScaling,
    generate_spiky_traffic,
)
from agent_smithers.latency_modelling.simulation import (
    CelerySimulation,
    SimulationParams,
)

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
    },
    {
        "name": "simulate_celery_latency",
        "description": "Simulate Celery worker latency with given parameters",
        "input_schema": {
            "type": "object",
            "properties": {
                "num_workers": {
                    "type": "integer",
                    "description": "Initial number of workers",
                },
                "service_time": {
                    "type": "integer",
                    "description": "Time to process each message in seconds",
                },
                "duration": {
                    "type": "integer",
                    "description": "Simulation duration in seconds",
                },
                "base_rate": {
                    "type": "integer",
                    "description": "Base message arrival rate",
                },
                "spike_rate": {
                    "type": "integer",
                    "description": "Peak message rate during spikes",
                },
                "worker_startup_delay": {
                    "type": "integer",
                    "description": "Time to start new workers in seconds",
                },
            },
            "required": [
                "num_workers",
                "service_time",
                "duration",
                "base_rate",
                "spike_rate",
            ],
        },
    },
    {
        "name": "get_simulation_plot",
        "description": "Get the latest simulation plot as a base64 encoded image",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "current_datetime",
        "description": "Get current datetime in ISO format with optional timezone",
        "input_schema": {
            "type": "object",
            "properties": {
                "timezone": {
                    "type": "string",
                    "description": "Optional timezone name (e.g. 'UTC', 'US/Pacific')",
                }
            },
            "required": [],
        },
    },
    {
        "name": "search_github",
        "description": "Search GitHub repositories matching a query within an organization",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query for repositories",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_github_code",
        "description": "Search for code within a specific repository",
        "input_schema": {
            "type": "object",
            "properties": {
                "repository": {
                    "type": "string",
                    "description": "The repository name",
                },
                "query": {
                    "type": "string",
                    "description": "The search query for code",
                },
            },
            "required": ["repository", "query"],
        },
    },
    {
        "name": "list_github_repos",
        "description": "List all GitHub repositories accessible",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
]

# Store latest simulation for plotting
_latest_simulation = None

def get_weather(*, location: str) -> str:
    return f"The weather in {location} is sunny."

def simulate_celery_latency(
    *,
    num_workers: int,
    service_time: int,
    duration: int,
    base_rate: int,
    spike_rate: int,
    worker_startup_delay: int = 20,
) -> str:
    global _latest_simulation

    # Generate traffic pattern
    traffic = generate_spiky_traffic(
        duration_seconds=duration,
        base_rate=base_rate,
        spike_rate=spike_rate,
        spike_duration=5,
        spike_interval=20,
    )

    # Configure simulation
    scaler = WorkerScaling(startup_delay=worker_startup_delay)
    params = SimulationParams(
        initial_workers=num_workers,
        service_time=service_time,
        duration=len(traffic),
        worker_scaling_func=scaler,
    )

    # Run simulation
    simulation = CelerySimulation(params, traffic)
    simulation.run()
    _latest_simulation = simulation

    # Get summary stats
    stats = simulation.get_summary_stats()
    return (
        f"Simulation completed with:\n"
        f"- Mean queue length: {stats['mean_queue_length']:.1f}\n"
        f"- Max queue length: {stats['max_queue_length']:.1f}\n"
        f"- Mean utilization: {stats['mean_utilization']:.1%}\n"
        f"- Mean wait time: {stats['mean_wait_time']:.1f}s\n"
        f"- Total completed: {stats['total_completed']}"
    )


def get_simulation_plot() -> str:
    """Get the latest simulation plot as base64 encoded PNG"""
    if _latest_simulation is None:
        return "No simulation has been run yet"

    # Create plot
    fig = _latest_simulation.plot_queue_dynamics()

    # Convert to base64
    buffer = BytesIO()
    fig.savefig(buffer, format="png")
    plt.close(fig)

    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{image_base64}"

def current_datetime(*, timezone: str | None = None) -> str:
    """Get current datetime, optionally in the specified timezone"""
    try:
        tz = ZoneInfo(timezone) if timezone else None
    except ZoneInfoNotFoundError:
        return f"Unknown timezone: {timezone}"

    dt = datetime.datetime.now(tz or datetime.UTC)
    return dt.isoformat()

github_client = GitHubClient(
    config=GitHubClientConfig(organization=env.GITHUB_ORGANIZATION)
)


def search_github(*, query: str) -> str:
    """Search GitHub repositories using the provided query"""
    try:
        repos = github_client.search_repositories(query)

        if not repos:
            return "No repositories found matching the query."

        results = [
            f"- {repo.full_name}\n"
            f"  Description: {repo.description or 'No description'}\n"
            f"  Stars: {repo.stargazers_count}, Forks: {repo.forks_count}\n"
            f"  URL: {repo.html_url}"
            for repo in repos[:5]  # Limit to top 5 results
        ]

        return "Top matching repositories:\n\n" + "\n\n".join(results)
    except Exception as e:
        return f"Error searching GitHub: {e!s}"


def search_github_code(*, repository: str, query: str) -> str:
    """Search for code within a GitHub repository"""
    try:
        results = github_client.search_code_in_repository(repository, query)

        if not results:
            return "No code matches found in the repository."

        formatted_results = []
        for result in results:
            formatted_results.append(
                f"File: {result['path']}\n"
                f"URL: {result['url']}\n"
                "```\n"
                f"{result['content']}\n"
                "```\n"
            )

        return "Matching code:\n\n" + "\n".join(formatted_results)
    except Exception as e:
        return f"Error searching GitHub code: {e!s}"


def list_github_repos() -> str:
    """List all GitHub repositories accessible"""
    try:
        repos = github_client.list_accessible_repositories()

        if not repos:
            return "No accessible repositories found."

        results = [
            f"- {repo.full_name}\n"
            f"  Description: {repo.description or 'No description'}\n"
            f"  URL: {repo.html_url}"
            for repo in repos[:10]  # Limit to top 10 results
        ]

        return "Accessible repositories:\n\n" + "\n\n".join(results)
    except Exception as e:
        return f"Error listing GitHub repositories: {e!s}"

def executor(block: ToolUseBlock):
    if block.name == "list_github_repos":
        return list_github_repos(**block.input)
    if block.name == "search_github_code":
        return search_github_code(**block.input)
    if block.name == "search_github":
        return search_github(**block.input)
    if block.name == "get_weather":
        return get_weather(**block.input)
    if block.name == "simulate_celery_latency":
        return simulate_celery_latency(**block.input)
    if block.name == "get_simulation_plot":
        return get_simulation_plot()
    if block.name == "current_datetime":
        return current_datetime(**block.input)

    return None
