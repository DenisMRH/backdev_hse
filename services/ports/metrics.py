from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

PredictionResult = Literal["violation", "no_violation"]
PredictionErrorType = Literal["model_unavailable", "prediction_error"]


class MetricsRecorder(Protocol):
    def record_prediction_result(self, *, result: PredictionResult) -> None: ...

    def observe_prediction_inference(self, *, inference_seconds: float) -> None: ...

    def observe_prediction_probability(self, *, probability: float) -> None: ...

    def record_prediction_error(self, *, error_type: PredictionErrorType) -> None: ...


@dataclass(frozen=True)
class NoopMetricsRecorder:
    def record_prediction_result(self, *, result: PredictionResult) -> None:
        return None

    def observe_prediction_inference(self, *, inference_seconds: float) -> None:
        return None

    def observe_prediction_probability(self, *, probability: float) -> None:
        return None

    def record_prediction_error(self, *, error_type: PredictionErrorType) -> None:
        return None


_recorder: MetricsRecorder = NoopMetricsRecorder()


def set_metrics_recorder(recorder: MetricsRecorder) -> None:
    global _recorder
    _recorder = recorder


def get_metrics_recorder() -> MetricsRecorder:
    return _recorder
