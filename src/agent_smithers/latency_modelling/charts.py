import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from rich.console import Console

console = Console()


def create_latency_plot(
    latency_series, arrival_rate, service_time: int, figsize=(12, 6)
) -> plt.Figure:
    """Create a plot showing latency and arrival rate over time"""
    if latency_series is None:
        console.print("[red]No latency data available to plot[/]")
        return None

    # Create figure with two y-axes
    fig, ax1 = plt.subplots(figsize=figsize)
    ax2 = ax1.twinx()

    # Set style
    sns.set_style("darkgrid")

    # Plot latency on primary y-axis
    sns.lineplot(
        data=latency_series,
        color="blue",
        alpha=0.7,
        ax=ax1,
        label="Latency",
    )

    # Plot arrival rate on secondary y-axis
    sns.lineplot(
        data=arrival_rate,
        color="green",
        alpha=0.7,
        ax=ax2,
        label="Arrival Rate",
    )

    # Add service time reference line
    ax1.axhline(
        y=service_time,
        color="r",
        linestyle="--",
        label="Minimum Latency (Service Time)",
    )

    # Customize plot
    ax1.set_xlabel("Time")
    ax1.set_ylabel("Latency (seconds)", color="blue")
    ax2.set_ylabel("Arrival Rate (requests/second)", color="green")

    # Adjust tick colors
    ax1.tick_params(axis="y", labelcolor="blue")
    ax2.tick_params(axis="y", labelcolor="green")

    plt.title("Request Latency and Arrival Rate Over Time")

    # Combine legends from both axes
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right")

    # Remove second legend to avoid duplication
    ax2.get_legend().remove()

    return fig


def create_queue_dynamics_plot(df: pd.DataFrame, figsize=(12, 12)) -> plt.Figure:
    """Plot queue dynamics over time"""
    # Create three subplots
    fig, (ax1, ax3, ax4) = plt.subplots(3, 1, figsize=figsize, sharex=True)
    ax2 = ax1.twinx()  # Create twin axis for queue length

    # Set style
    sns.set_style("darkgrid")

    # First subplot (arrivals and queue) - unchanged
    sns.lineplot(
        data=df,
        x="timestamp",
        y="arrivals",
        ax=ax1,
        label="Messages/Second",
        color="blue",
    )
    ax1.set_ylabel("Messages per Second", color="blue")
    ax1.tick_params(axis="y", labelcolor="blue")

    # Plot queue length on right y-axis
    sns.lineplot(
        data=df, x="timestamp", y="in_queue", ax=ax2, label="Queue Length", color="red"
    )
    ax2.set_ylabel("Queue Length", color="red")
    ax2.tick_params(axis="y", labelcolor="red")

    # Set first subplot title
    ax1.set_title("System Load")

    # Second subplot (wait times) - unchanged
    sns.lineplot(
        data=df,
        x="timestamp",
        y="mean_wait_time",
        ax=ax3,
        label="Mean Wait Time",
        color="green",
    )
    sns.lineplot(
        data=df,
        x="timestamp",
        y="max_wait_time",
        ax=ax3,
        label="Max Wait Time",
        color="red",
        alpha=0.5,
    )
    sns.lineplot(
        data=df,
        x="timestamp",
        y="min_wait_time",
        ax=ax3,
        label="Min Wait Time",
        color="blue",
        alpha=0.5,
    )

    ax3.set_title("Queue Wait Times Over Time")
    ax3.set_ylabel("Seconds")
    ax3.set_xlabel("Time")
    ax3.legend()

    # Third subplot - Worker utilization
    sns.lineplot(
        data=df,
        x="timestamp",
        y="in_progress",
        ax=ax4,
        label="Active Workers",
        color="purple",
    )
    ax4.axhline(
        y=df["in_progress"].max(),
        color="r",
        linestyle="--",
        label=f"Worker Limit ({df['in_progress'].max()})",
    )
    ax4.set_title("Worker Utilization Over Time")
    ax4.set_ylabel("Number of Workers")
    ax4.set_xlabel("Time")
    ax4.legend()

    # Combine legends for first subplot
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right")
    ax2.get_legend().remove()  # Remove duplicate legend

    plt.tight_layout()
    return fig
