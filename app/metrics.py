from __future__ import annotations

from prometheus_client import Counter, Histogram

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    labelnames=("method", "endpoint", "status"),
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    labelnames=("method", "endpoint"),
)

PREDICTIONS_TOTAL = Counter(
    "predictions_total",
    "Total number of predictions",
    labelnames=("result",),
)

PREDICTION_DURATION_SECONDS = Histogram(
    "prediction_duration_seconds",
    "Model inference duration in seconds",
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

PREDICTION_ERRORS_TOTAL = Counter(
    "prediction_errors_total",
    "Total number of prediction errors",
    labelnames=("error_type",),
)

DB_QUERY_DURATION_SECONDS = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    labelnames=("query_type",),
)

MODEL_PREDICTION_PROBABILITY = Histogram(
    "model_prediction_probability",
    "Distribution of prediction probability",
    buckets=(
        0.0,
        0.01,
        0.05,
        0.1,
        0.2,
        0.3,
        0.4,
        0.5,
        0.6,
        0.7,
        0.8,
        0.9,
        0.95,
        0.99,
        1.0,
    ),
)
