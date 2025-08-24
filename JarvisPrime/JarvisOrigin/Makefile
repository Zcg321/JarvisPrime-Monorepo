
.PHONY: deps synth tok pretrain sft serve

deps:    ; pip install -r requirements.txt

synth:    ; python -m src.dataforge.gen_corpus
tok:      ; python -m src.core.build_tokenizer
pretrain: ; python -m src.train.pretrain
sft:      ; python -m src.train.sft
serve:    ; python -m uvicorn src.serve.server:APP --host 0.0.0.0 --port 8000
