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


def main():
    # Generate 4 minutes of spiky traffic (2 min active, 2 min silent)
    message_traffic = generate_spiky_traffic(
        duration_seconds=120,
        base_rate=1,
        spike_rate=25,
        spike_duration=5,
        spike_interval=20,
    )

    params = SimulationParams(
        num_workers=45, service_time=5, duration=len(message_traffic)
    )
    simulation = CelerySimulation(params, message_traffic)
    simulation.run()

    # Plot queue dynamics
    simulation.plot_queue_dynamics()
    plt.show()


if __name__ == "__main__":
    main()
