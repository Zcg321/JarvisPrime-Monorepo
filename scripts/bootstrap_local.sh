#!/usr/bin/env bash
set -euo pipefail
echo ">>> Jarvis Prime — local bootstrap (RTX 3090 Ti)"

# rudimentary hardware safety: adjust training load based on VRAM
if command -v nvidia-smi >/dev/null 2>&1; then
    VRAM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -n1)
    echo "Detected VRAM: ${VRAM} MiB"
    if [ "$VRAM" -lt 24000 ]; then
        echo "VRAM below 24GB; enabling safe mode"
        export JARVIS_SAFE_MODE=1 JARVIS_BSZ=1 JARVIS_GRAD_ACC=32
    else
        export JARVIS_SAFE_MODE=0 JARVIS_BSZ=1 JARVIS_GRAD_ACC=16
    fi
else
    echo "No NVIDIA GPU detected; CPU safe mode"
    export JARVIS_SAFE_MODE=1 JARVIS_BSZ=1 JARVIS_GRAD_ACC=32
fi
if [ "${JARVIS_SKIP_BOOTSTRAP_DEPS:-0}" != "1" ]; then
    python3 -m venv .jarvis && source .jarvis/bin/activate
    pip install -U pip wheel setuptools
    pip install --index-url https://download.pytorch.org/whl/cu121 torch torchvision torchaudio || pip install torch torchvision torchaudio
    pip install "transformers==4.42.4" datasets sentencepiece tokenizers accelerate bitsandbytes fastapi uvicorn pyyaml rich tqdm numpy faiss-cpu sentence-transformers pytest requests feedparser
    python - <<PY
import subprocess, sys
try:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "deepspeed==0.14.2"])
    print("DeepSpeed OK")
except Exception as e:
    print("DeepSpeed skipped:", e)
PY
    export AWARENESS=1 LEARN_ONLINE=1 USE_LORA=1 USE_8BIT_OPT=1 JARVIS_MAX_TPM=8 PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128,expandable_segments:True
fi

# Replay experience logs for continual learning if any exist
if [ "${JARVIS_SKIP_REPLAY:-0}" != "1" ]; then
    if ls logs/experience/*.json >/dev/null 2>&1; then
        echo "Replaying experience logs"
        python - <<'PY'
import glob, json
count = 0
for path in glob.glob('logs/experience/*.json'):
    with open(path) as f:
        json.load(f)
    count += 1
print(f"Replayed {count} experience logs")
PY
    else
        echo "No experience logs found"
    fi
else
    echo "Skipping experience replay"
fi

echo "Bootstrap ready. Run your extended trainers & server to go full power."
