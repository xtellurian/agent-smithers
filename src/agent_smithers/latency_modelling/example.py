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


def main():
    # Generate 2 minutes of message traffic (1 min active, 1 min silent)
    message_traffic = generate_message_traffic(240)

    params = SimulationParams(
        num_workers=12, service_time=5, duration=len(message_traffic)
    )
    simulation = CelerySimulation(params, message_traffic)
    simulation.run()

    # Plot queue dynamics
    simulation.plot_queue_dynamics()
    plt.show()


if __name__ == "__main__":
    main()
