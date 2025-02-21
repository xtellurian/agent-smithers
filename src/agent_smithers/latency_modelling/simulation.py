from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable

import matplotlib.pyplot as plt
import pandas as pd
from charts import create_queue_dynamics_plot
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)


@dataclass
class SimulationParams:
    initial_workers: int
    service_time: int  # seconds
    duration: int  # seconds
    worker_scaling_func: Callable[
        [int, int], int
    ]  # takes (queue_length, seconds), returns num_workers
    log_interval: int = 60  # Log detailed metrics every N seconds


@dataclass
class Message:
    id: int
    arrival_time: datetime
    queue_position: int = 0  # Track position in queue

    def wait_time(self, current_time: datetime) -> float:
        """Calculate how long this message has been waiting"""
        return (current_time - self.arrival_time).total_seconds()


class CelerySimulation:
    def __init__(self, params: SimulationParams, arrival_rate: pd.Series):
        self.params = params
        self.arrival_rate = arrival_rate
        self._validate_inputs()
        self.df = self._initialize_dataframe()
        self.message_counter = 0
        self.message_queue = deque[Message]()  # Queue of Message objects
        self.in_progress: list[Message] = []  # List of currently processing messages
        self.console = Console()
        self.queue_position = 0  # Track overall queue position
        self.current_workers = params.initial_workers

    def _validate_inputs(self):
        if len(self.arrival_rate) != self.params.duration:
            raise ValueError(
                f"Arrival rate series must have {self.params.duration} entries"
            )

    def _initialize_dataframe(self) -> pd.DataFrame:
        """Initialize the simulation DataFrame"""
        df = pd.DataFrame(
            {
                "timestamp": pd.date_range(
                    start="2024-01-01", periods=self.params.duration, freq="s"
                ),
                "arrivals": self.arrival_rate.to_numpy(),
                "in_queue": 0,
                "in_progress": 0,
                "completed": 0,
                "min_wait_time": 0.0,
                "mean_wait_time": 0.0,
                "max_wait_time": 0.0,
                "utilization": 0.0,
                "num_workers": self.params.initial_workers,
            }
        )
        return df

    def _create_message(self, current_time: datetime) -> Message:
        """Create a new message with unique ID and queue position"""
        self.message_counter += 1
        self.queue_position += 1
        return Message(
            id=self.message_counter,
            arrival_time=current_time,
            queue_position=self.queue_position,
        )

    def _update_worker_count(self, queue_length: int, seconds_elapsed: int) -> None:
        """Update number of workers based on scaling function"""
        self.current_workers = self.params.worker_scaling_func(
            queue_length, seconds_elapsed
        )

    def run(self) -> pd.DataFrame:
        """Run the simulation for the specified duration with progress tracking"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
        ) as progress:
            task = progress.add_task("[cyan]Running simulation...", total=len(self.df))

            for i in range(len(self.df)):
                current_time = self.df.iloc[i]["timestamp"]

                # Update worker count based on current queue length and time
                self._update_worker_count(len(self.message_queue), i)

                # Process completions
                if i > 0:
                    completions = int(len(self.in_progress) / self.params.service_time)
                    self.in_progress = self.in_progress[completions:]

                # Process new arrivals
                new_arrivals = int(self.df.iloc[i]["arrivals"])
                new_messages = [
                    self._create_message(current_time) for _ in range(new_arrivals)
                ]

                # Calculate available capacity using current worker count
                available_capacity = self.current_workers - len(self.in_progress)

                # Process queue first (FIFO order guaranteed by deque)
                while available_capacity > 0 and self.message_queue:
                    msg = (
                        self.message_queue.popleft()
                    )  # Always takes from front of queue
                    wait_time = msg.wait_time(current_time)
                    self.in_progress.append(msg)
                    available_capacity -= 1

                    # Log queue position and wait time for verification
                    if i % self.params.log_interval == 0:
                        self.console.print(
                            f"[blue]Processing message {msg.id} "
                            f"(queue position {msg.queue_position}, "
                            f"wait time {wait_time:.1f}s)"
                        )

                # Process new arrivals (add to back of queue if no capacity)
                for msg in new_messages:
                    if available_capacity > 0:
                        self.in_progress.append(msg)
                        available_capacity -= 1
                    else:
                        self.message_queue.append(msg)  # Adds to back of queue

                # Calculate metrics
                current_queue_length = len(self.message_queue)

                # Calculate current wait times for all messages in queue
                if current_queue_length > 0:
                    current_wait_times = [
                        msg.wait_time(current_time) for msg in self.message_queue
                    ]
                    self.df.at[i, "min_wait_time"] = min(current_wait_times)
                    self.df.at[i, "mean_wait_time"] = sum(current_wait_times) / len(
                        current_wait_times
                    )
                    self.df.at[i, "max_wait_time"] = max(current_wait_times)
                else:
                    self.df.at[i, "min_wait_time"] = 0
                    self.df.at[i, "mean_wait_time"] = 0
                    self.df.at[i, "max_wait_time"] = 0

                # Update DataFrame
                self.df.at[i, "in_queue"] = current_queue_length
                self.df.at[i, "in_progress"] = len(self.in_progress)
                self.df.at[i, "completed"] = completions if i > 0 else 0
                self.df.at[i, "num_workers"] = self.current_workers
                self.df.at[i, "utilization"] = (
                    len(self.in_progress) / self.current_workers
                )

                # Log detailed metrics at intervals
                if i % self.params.log_interval == 0:
                    self.console.print(
                        f"[green]Time: {current_time.strftime('%H:%M:%S')} "
                        f"Queue: {len(self.message_queue)} "
                        f"Processing: {len(self.in_progress)} "
                        f"Completed: {self.df['completed'].sum()}"
                    )

                progress.update(task, advance=1)

        self.console.print(
            f"[bold green]Simulation completed! Processed {self.message_counter} messages."
        )
        return self.df

    def get_summary_stats(self) -> dict:
        """Calculate summary statistics from the simulation"""
        return {
            "mean_queue_length": self.df["in_queue"].mean(),
            "max_queue_length": self.df["in_queue"].max(),
            "mean_utilization": self.df["utilization"].mean(),
            "peak_utilization": self.df["utilization"].max(),
            "total_completed": self.df["completed"].sum(),
            "mean_wait_time": self.df["queue_wait_time"].mean(),
            "max_wait_time": self.df["queue_wait_time"].max(),
        }

    def plot_queue_dynamics(self) -> plt.Figure:
        """Plot queue dynamics over time"""
        return create_queue_dynamics_plot(self.df)
