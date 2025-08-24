import os, json
from tokenizers import Tokenizer
from tokenizers.models import BPE
from tokenizers.trainers import BpeTrainer
from tokenizers.pre_tokenizers import Whitespace

DATA_DIRS = ["data/dna","data/corpus","data/gen"]
SPECIALS = ["<|bos|>","<|eos|>","<|pad|>"]
os.makedirs("artifacts", exist_ok=True)

def files():
    for d in DATA_DIRS:
        for r,_,fs in os.walk(d):
            for f in fs:
                if f.endswith((".txt",".md",".json",".jsonl",".py",".yml",".yaml")):
                    yield os.path.join(r,f)

paths = list(files())
if not paths: raise SystemExit("Add text to data/dna or run `make synth` first.")
tok = Tokenizer(BPE(unk_token="<|pad|>"))
tok.pre_tokenizer = Whitespace()
tok.train(files=paths, trainer=BpeTrainer(vocab_size=50000, special_tokens=SPECIALS, show_progress=True))
tok.save("artifacts/tokenizer.json")
json.dump({"bos_token":"<|bos|>","eos_token":"<|eos|>","pad_token":"<|pad|>"}, open("artifacts/tokenizer_config.json","w"))
print("✅ tokenizer saved -> artifacts/")
