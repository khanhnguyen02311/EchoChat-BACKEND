import time
from typing import Tuple
from configurations import conf
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor


# from prometheus_client.openmetrics.exposition import generate_latest
# from prometheus_client import Histogram, Gauge, Counter, REGISTRY, CONTENT_TYPE_LATEST
# from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
# from starlette.requests import Request
# from starlette.responses import Response
# from fastapi import status
# from starlette.routing import Match


# INFO = Gauge(
#     "fastapi_app_info", "FastAPI application information.", [
#         "app_name"]
# )
# REQUESTS = Counter(
#     "fastapi_requests_total", "Total count of requests by method and path.", [
#         "method", "path", "app_name"]
# )
# RESPONSES = Counter(
#     "fastapi_responses_total",
#     "Total count of responses by method, path and status codes.",
#     ["method", "path", "status_code", "app_name"],
# )
# REQUESTS_PROCESSING_TIME = Histogram(
#     "fastapi_requests_duration_seconds",
#     "Histogram of requests processing time by path (in seconds)",
#     ["method", "path", "app_name"],
# )
# EXCEPTIONS = Counter(
#     "fastapi_exceptions_total",
#     "Total count of exceptions raised by path and exception type",
#     ["method", "path", "exception_type", "app_name"],
# )
# REQUESTS_IN_PROGRESS = Gauge(
#     "fastapi_requests_in_progress",
#     "Gauge of requests by method and path currently being processed",
#     ["method", "path", "app_name"],
# )
#
#
# class PrometheusMiddleware(BaseHTTPMiddleware):
#     def __init__(self, app) -> None:
#         super().__init__(app)
#         self.app_name = conf.Observability.METRICS_SERVICE_NAME + "-" + conf.Env.APP_STAGE
#         INFO.labels(app_name=self.app_name).inc()
#
#     async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
#         method = request.method
#         path, is_handled_path = self.get_path(request)
#
#         if not is_handled_path:
#             return await call_next(request)
#
#         REQUESTS_IN_PROGRESS.labels(
#             method=method, path=path, app_name=self.app_name).inc()
#         REQUESTS.labels(method=method, path=path, app_name=self.app_name).inc()
#         before_time = time.perf_counter()
#         try:
#             response = await call_next(request)
#         except BaseException as e:
#             status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
#             EXCEPTIONS.labels(method=method, path=path, exception_type=type(
#                 e).__name__, app_name=self.app_name).inc()
#             raise e from None
#         else:
#             status_code = response.status_code
#             after_time = time.perf_counter()
#             # retrieve trace id for exemplar
#             span = trace.get_current_span()
#             trace_id = trace.format_trace_id(
#                 span.get_span_context().trace_id)
#
#             REQUESTS_PROCESSING_TIME.labels(method=method, path=path, app_name=self.app_name).observe(
#                 after_time - before_time, exemplar={'TraceID': trace_id}
#             )
#         finally:
#             RESPONSES.labels(method=method, path=path,
#                              status_code=status_code, app_name=self.app_name).inc()
#             REQUESTS_IN_PROGRESS.labels(
#                 method=method, path=path, app_name=self.app_name).dec()
#
#         return response
#
#     @staticmethod
#     def get_path(request: Request) -> Tuple[str, bool]:
#         for route in request.app.routes:
#             match, child_scope = route.matches(request.scope)
#             if match == Match.FULL:
#                 return route.path, True
#
#         return request.url.path, False
#
#
# def metrics(request: Request) -> Response:
#     return Response(generate_latest(REGISTRY), headers={"Content-Type": CONTENT_TYPE_LATEST})


def setting_otlp(app, log_correlation: bool = True) -> None:
    """Setting OpenTelemetry and set the service name to show in traces"""

    resource = Resource.create(attributes={
        "service.name": conf.Observability.OBSERVABILITY_SERVICE_NAME + "-" + conf.Env.APP_STAGE,  # for Tempo to distinguish source
        "compose_service": conf.Observability.OBSERVABILITY_SERVICE_NAME + "-" + conf.Env.APP_STAGE  # as a query criteria for Trace to logs
    })

    # set the tracer provider
    tracer = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer)

    tracer.add_span_processor(BatchSpanProcessor(
        OTLPSpanExporter(endpoint=conf.Observability.TRACING_ENDPOINT)))

    if log_correlation:
        LoggingInstrumentor().instrument(set_logging_format=True)

    FastAPIInstrumentor.instrument_app(app, tracer_provider=tracer)
