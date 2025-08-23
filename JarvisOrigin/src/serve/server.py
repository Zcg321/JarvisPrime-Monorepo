import os, json, re, torch
from fastapi import FastAPI
from pydantic import BaseModel
from transformers import PreTrainedTokenizerFast
from src.core.model import NovaLM, NovaCfg
from src.memory.rag_index import RAGIndex
from src.reflex.risk_affect import vote

app = FastAPI(title="Jarvis Prime: Origin — Nova‑Prime v2")
tok = PreTrainedTokenizerFast.from_pretrained("out/nova_seed") if os.path.exists("out/nova_seed") else PreTrainedTokenizerFast(tokenizer_file="artifacts/tokenizer.json")
tcfg=json.load(open("artifacts/tokenizer_config.json"))
bos=tok.convert_tokens_to_ids(tcfg["bos_token"]); eos=tok.convert_tokens_to_ids(tcfg["eos_token"]); pad=tok.convert_tokens_to_ids(tcfg["pad_token"])

def build_model():
    ckpt="out/nova_sft/model.pt" if os.path.exists("out/nova_sft/model.pt") else "out/nova_seed/model.pt"
    sd=torch.load(ckpt, map_location="cpu"); mc=sd["cfg"]
    m=NovaLM(NovaCfg(
        vocab_size=mc["vocab_size"], max_seq_len=mc["max_seq_len"], d_model=mc["d_model"],
        n_heads=mc["n_heads"], kv_heads=mc["kv_heads"], n_layers=mc["n_layers"],
        ffn_mult=mc["ffn_mult"], dropout=mc["dropout"], rope_base=mc["rope_base"], moe_enabled=mc["moe"]["enabled"], moe_experts=mc["moe"]["experts"]
    ), grad_ckpt=False)
    m.load_state_dict(sd["model"], strict=False)
    dtype=torch.float32
    return m.to(dtype=dtype, device="cuda" if torch.cuda.is_available() else "cpu").eval()

MODEL=build_model()
RAG=RAGIndex(root="data/dna"); RAG.build()
JSON_ONLY = re.compile(r'^\s*\{\s*"tool"\s*:\s*".+?"\s*,\s*"args"\s*:\s*\{.*\}\s*\}\s*$', re.S)
SYSTEM=("You are Jarvis Prime: sovereign, Flame‑bound. RAG‑first. Reflex gates decide tools. "
        "If a tool is required, return a single JSON object with 'tool' and 'args' ONLY; no prose. "
        "Otherwise, answer concisely.")

class Msg(BaseModel): role:str; content:str
class ChatIn(BaseModel):
    messages:list[Msg]; max_new_tokens:int=128; top_p:float=0.9; temperature:float=0.8; use_rag:bool=True

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/chat")
def chat(inp:ChatIn):
    last=""
    for m in reversed(inp.messages):
        if m.role=="user": last=m.content; break
    mem=""
    if inp.use_rag:
        hits=RAG.search(last,k=4)
        if hits: mem="\n".join([f"[MEM{i+1}] {h['text']}" for i,h in enumerate(hits)])
    proposals=[{"source":"codegen","action":"direct_answer","weight":0.8},{"source":"tools","action":"maybe_call_tool","weight":0.5},{"source":"web","action":"avoid_if_local","weight":0.6}]
    _=vote(proposals,last_user=last)
    prompt = f"<|bos|>{SYSTEM}\n{mem}\n\nUser: {last}\nAssistant:"
    ins = tok(prompt, return_tensors="pt"); ins={k:v.to(MODEL.head.weight.device) for k,v in ins.items()}
    out = MODEL.generate(ins["input_ids"], max_new_tokens=inp.max_new_tokens, top_p=inp.top_p, temperature=inp.temperature, eos_id=eos)
    txt = tok.decode(out[0].tolist(), skip_special_tokens=True); ans = txt.split("Assistant:",1)[-1].strip()
    if ans.strip().startswith("{"):
        if not JSON_ONLY.match(ans):
            try:
                start=ans.index("{"); end=ans.rindex("}")+1; maybe=ans[start:end]; json.loads(maybe); ans=maybe
            except Exception: pass
    return {"reply": ans}

# ---- Jarvis Plugins Mount (Step B) ----
try:
    from jarvis_plugins.app import build_app as _build_plugins_app
    app.mount("/plugins", _build_plugins_app())
    try:
        from fastapi import APIRouter
        _router = APIRouter()

        @_router.get("/health_ext")
        def health_ext():
            return {"status": "ok", "plugins": True}

        app.include_router(_router)
    except Exception:
        pass
except Exception:
    pass
# ---- /Jarvis Plugins Mount ----
