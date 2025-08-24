from .metrics import METRICS


def exposition() -> str:
    snap = METRICS.snapshot()
    lines = [
        f"requests_total {snap['requests_total']}",
        f"errors_total {snap['errors_total']}",
        f"latency_p95{{runtime='fp16'}} {METRICS._p95(METRICS.lat_fp16):.3f}",
        f"latency_p95{{runtime='int8'}} {METRICS._p95(METRICS.lat_int8):.3f}",
        f"savepoints_written_total {snap['savepoints_written']}",
        f"alerts_total {snap['alerts_total']}",
        f"ratelimit_drops_total {snap['ratelimit_drops']}",
    ]
    return "\n".join(lines) + "\n"
