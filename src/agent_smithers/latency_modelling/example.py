import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from simulation import CelerySimulation, SimulationParams


def generate_message_traffic(duration_seconds: int = 3600) -> pd.Series:
    """Generate number of messages arriving each second"""
    # Generate time index
    index = pd.date_range(
        start="2024-01-01",
        periods=duration_seconds * 2,  # Double the duration
        freq="s",
    )

    # Generate message counts for first half
    base_count = np.round(
        10 + 5 * np.sin(2 * np.pi * np.arange(duration_seconds) / 3600)
    )
    random_variation = np.random.randint(-2, 3, duration_seconds)  # -2 to +2 messages
    message_counts = np.maximum(base_count + random_variation, 0).astype(int)

    # Add silent period
    silent_period = np.zeros(duration_seconds, dtype=int)

    # Combine active and silent periods
    full_traffic = np.concatenate([message_counts, silent_period])

    return pd.Series(full_traffic, index=index, name="messages_per_second")


def generate_spiky_traffic(
    duration_seconds: int = 3600,
    base_rate: int = 5,
    spike_rate: int = 30,
    spike_duration: int = 10,
    spike_interval: int = 60,
) -> pd.Series:
    """Generate message traffic with periodic spikes

    Args:
        duration_seconds: Total duration to generate traffic for
        base_rate: Normal message rate between spikes
        spike_rate: Peak message rate during spikes
        spike_duration: How long each spike lasts in seconds
        spike_interval: Seconds between start of each spike
    """
    # Generate time index for full duration (active + silent)
    index = pd.date_range(
        start="2024-01-01",
        periods=duration_seconds * 2,
        freq="s",
    )

    # Create base traffic
    traffic = np.full(duration_seconds, base_rate, dtype=int)

    # Add spikes
    for spike_start in range(0, duration_seconds, spike_interval):
        if spike_start + spike_duration > duration_seconds:
            break

        # Create spike with random variation
        spike = np.random.randint(spike_rate - 5, spike_rate + 5, spike_duration)
        traffic[spike_start : spike_start + spike_duration] = spike

    # Add silent period
    silent_period = np.zeros(duration_seconds, dtype=int)
    full_traffic = np.concatenate([traffic, silent_period])

    return pd.Series(full_traffic, index=index, name="messages_per_second")


class WorkerScaling:
    def __init__(self, startup_delay: int = 20):
        self.startup_delay = startup_delay
        self.scale_up_time = None  # When we started scaling up
        self.target_workers = 10  # Initial worker count
        self.current_workers = 10  # Current active workers

    def __call__(self, queue_length: int, seconds: int) -> int:
        # Determine target worker count based on queue length
        new_target = 45 if queue_length >= 50 else 30 if queue_length >= 10 else 10

        # If target has changed, record the time
        if new_target > self.target_workers:
            if self.scale_up_time is None:
                self.scale_up_time = seconds
            self.target_workers = new_target
        elif new_target < self.target_workers:
            # Scale down happens immediately
            self.target_workers = new_target
            self.current_workers = new_target
            self.scale_up_time = None

        # If we're scaling up and enough time has passed
        if (
            self.scale_up_time is not None
            and seconds >= self.scale_up_time + self.startup_delay
        ):
            self.current_workers = self.target_workers
            self.scale_up_time = None

        return self.current_workers


def main():
    # Generate 4 minutes of spiky traffic (2 min active, 2 min silent)
    message_traffic = generate_spiky_traffic(
        duration_seconds=120,
        base_rate=1,
        spike_rate=25,
        spike_duration=5,
        spike_interval=20,
    )

    scaler = WorkerScaling(startup_delay=20)  # 20 second worker startup time
    params = SimulationParams(
        initial_workers=10,
        service_time=5,
        duration=len(message_traffic),
        worker_scaling_func=scaler,
    )
    simulation = CelerySimulation(params, message_traffic)
    simulation.run()

    # Plot queue dynamics
    simulation.plot_queue_dynamics()
    plt.show()


if __name__ == "__main__":
    main()
