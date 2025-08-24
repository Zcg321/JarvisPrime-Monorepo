from src.serve.metrics import Metrics


def test_error_budget_decrements():
    m = Metrics()
    m.slo = {'availability':1.0,'p95_latency_int8':0.0,'p95_latency_fp16':0.0,'error_budget_day':1,'error_budget_week':1}
    m.error_budget_day = 1
    m.error_budget_week = 1
    m.requests_total = 1
    m.errors_total = 1
    m._check_slo()
    assert m.error_budget_day == 0
    assert m.error_budget_week == 0
    assert m._budget_alerted
