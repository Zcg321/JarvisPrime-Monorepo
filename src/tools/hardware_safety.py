from typing import Dict

def gpu_info() -> Dict[str, float]:
    """Return GPU name and total memory in GB if available."""
    info = {"name": "cpu", "total_gb": 0.0}
    try:
        import torch  # type: ignore
        if torch.cuda.is_available():
            props = torch.cuda.get_device_properties(0)
            info = {"name": props.name, "total_gb": props.total_memory / (1024**3)}
    except Exception:
        pass
    return info


def recommend_config(min_gb: float = 24.0) -> Dict[str, int]:
    """Return safe micro batch and grad accum based on VRAM.

    Defaults to CPU-safe values when no GPU or insufficient VRAM.
    """
    info = gpu_info()
    if info["total_gb"] >= min_gb:
        return {"micro_bsz": 1, "grad_accum": 16}
    return {"micro_bsz": 1, "grad_accum": 32}
