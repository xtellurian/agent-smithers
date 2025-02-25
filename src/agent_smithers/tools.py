import base64
from io import BytesIO

import matplotlib.pyplot as plt
from anthropic.types import ToolUseBlock
from latency_modelling.example import WorkerScaling, generate_spiky_traffic
from latency_modelling.simulation import CelerySimulation, SimulationParams

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

def executor(block: ToolUseBlock):
    if block.name == "get_weather":
        return get_weather(**block.input)
    elif block.name == "simulate_celery_latency":
        return simulate_celery_latency(**block.input)
    elif block.name == "get_simulation_plot":
        return get_simulation_plot()

    return None
