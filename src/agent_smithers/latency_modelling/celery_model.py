from dataclasses import dataclass

import numpy as np
import math
from rich.console import Console
from rich.table import Table


@dataclass
class CeleryLatencyModel:
    num_workers: int
    arrival_rate: float  # requests per second
    service_time: float  # seconds per request

    def __post_init__(self):
        self.console = Console()
        self._validate_inputs()

    def _validate_inputs(self):
        if self.num_workers <= 0:
            raise ValueError("Number of workers must be positive")
        if self.arrival_rate < 0:
            raise ValueError("Arrival rate must be non-negative")
        if self.service_time <= 0:
            raise ValueError("Service time must be positive")

    @property
    def utilization(self) -> float:
        """Calculate worker utilization (ρ = λ/(μc))"""
        service_rate = 1 / self.service_time  # μ
        return self.arrival_rate / (service_rate * self.num_workers)

    @property
    def is_stable(self) -> bool:
        """Check if the system is stable (utilization < 1)"""
        return self.utilization < 1

    @property
    def max_throughput(self) -> float:
        """Maximum possible requests per second"""
        return self.num_workers / self.service_time

    def average_queue_length(self) -> float | None:
        """Calculate average number of requests in queue using M/M/c formula"""
        if not self.is_stable:
            return None

        rho = self.utilization
        c = self.num_workers

        # Erlang C formula
        p0 = self._calculate_p0()
        lq = (p0 * (self.arrival_rate * self.service_time) ** c * rho) / (
            self.num_workers * (1 - rho) ** 2 * math.factorial(c)
        )
        return lq

    def _calculate_p0(self) -> float:
        """Calculate p0 for Erlang C formula"""
        c = self.num_workers
        rho = self.utilization
        lambda_mu = self.arrival_rate * self.service_time

        sum_term = sum((lambda_mu**n) / math.factorial(n) for n in range(c))
        last_term = (lambda_mu**c) / (math.factorial(c) * (1 - rho))

        return 1 / (sum_term + last_term)

    def average_waiting_time(self) -> float | None:
        """Calculate average waiting time in queue"""
        if not self.is_stable:
            return None

        lq = self.average_queue_length()
        if lq is None:
            return None

        return lq / self.arrival_rate

    def average_total_time(self) -> float | None:
        """Calculate total time (waiting + service)"""
        wait_time = self.average_waiting_time()
        if wait_time is None:
            return None
        return wait_time + self.service_time

    def _get_stability_explanation(self) -> str:
        """Generate explanation for why system is unstable"""
        current_load = self.arrival_rate * self.service_time
        max_capacity = self.num_workers
        overflow = current_load - max_capacity

        return (
            f"[red]System is unstable![/] "
            f"Current load ({current_load:.1f} worker-seconds) exceeds "
            f"maximum capacity ({max_capacity} workers). "
            f"Need {int(np.ceil(overflow / self.service_time))} additional workers "
            f"or reduce arrival rate by {(self.arrival_rate - self.max_throughput):.1f} req/s"
        )

    def print_metrics(self):
        """Print all metrics in a formatted table"""
        table = Table(title="Celery Worker Latency Metrics")

        table.add_column("Metric", justify="left", style="cyan")
        table.add_column("Value", justify="right", style="green")

        metrics = [
            ("Number of Workers", self.num_workers),
            ("Arrival Rate (req/s)", f"{self.arrival_rate:.2f}"),
            ("Service Time (s)", f"{self.service_time:.2f}"),
            ("Worker Utilization", f"{self.utilization:.2%}"),
            ("System Stable", "✅" if self.is_stable else "❌"),
            ("Max Throughput (req/s)", f"{self.max_throughput:.2f}"),
        ]

        if self.is_stable:
            wait_time = self.average_waiting_time()
            total_time = self.average_total_time()
            queue_length = self.average_queue_length()

            metrics.extend(
                [
                    ("Avg Queue Length", f"{queue_length:.2f}"),
                    ("Avg Waiting Time (s)", f"{wait_time:.2f}"),
                    ("Avg Total Time (s)", f"{total_time:.2f}"),
                ]
            )
        else:
            self.console.print(self._get_stability_explanation())

        for metric, value in metrics:
            table.add_row(metric, str(value))

        self.console.print(table)
