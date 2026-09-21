import os

import mlflow


def configure_tracking(experiment: str) -> None:
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "file:./mlruns"))
    mlflow.set_experiment(experiment)

