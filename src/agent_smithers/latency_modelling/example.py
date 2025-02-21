from celery_model import CeleryLatencyModel


def main():
    # Example: 5 workers, 10 req/sec, 0.5s service time
    model = CeleryLatencyModel(num_workers=6, arrival_rate=10, service_time=0.5)

    model.print_metrics()


if __name__ == "__main__":
    main()
