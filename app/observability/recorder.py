from __future__ import annotations

from services.ports.metrics import MetricsRecorder, PredictionErrorType, PredictionResult

from app.metrics import (
    MODEL_PREDICTION_PROBABILITY,
    PREDICTION_DURATION_SECONDS,
    PREDICTION_ERRORS_TOTAL,
    PREDICTIONS_TOTAL,
)


class PrometheusMetricsRecorder(MetricsRecorder):
    def record_prediction_result(self, *, result: PredictionResult) -> None:
        PREDICTIONS_TOTAL.labels(result=result).inc()

    def observe_prediction_inference(self, *, inference_seconds: float) -> None:
        PREDICTION_DURATION_SECONDS.observe(inference_seconds)

    def observe_prediction_probability(self, *, probability: float) -> None:
        MODEL_PREDICTION_PROBABILITY.observe(probability)

    def record_prediction_error(self, *, error_type: PredictionErrorType) -> None:
        PREDICTION_ERRORS_TOTAL.labels(error_type=error_type).inc()
