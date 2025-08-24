# --- STEP_C_SAVEPOINTS ---
import os as _os_stepc
try:
    from jarvis_plugins.savepoint import SavepointLogger as _SP_Cls
    _SP_STEP=_SP_Cls()
except Exception:
    _SP_STEP=None
_STEP_INTERVAL=int(_os_stepc.getenv("JARVIS_TRAIN_SAVEPOINT_EVERY","50"))

def _train_savepoint(step:int, loss:float, extra:dict):
    if _SP_STEP and _STEP_INTERVAL>0 and step % _STEP_INTERVAL==0:
        try:
            _SP_STEP.create({
                "phase": extra.get("phase","unknown"),
                "step": step,
                "loss": float(loss),
                "lr": float(extra.get("lr",0.0)),
                "notes": extra.get("notes","")
            }, tag="train")
        except Exception:
            pass
# --- /STEP_C_SAVEPOINTS ---
import os, json, torch
from datasets import load_dataset
from transformers import PreTrainedTokenizerFast
from torch.utils.data import DataLoader
from torch.optim import AdamW
from torch.nn.utils import clip_grad_norm_
from src.core.model import NovaLM, NovaCfg
import yaml

CFG = yaml.safe_load(open("configs/nova_1p3b.yaml"))
tok = PreTrainedTokenizerFast(tokenizer_file="artifacts/tokenizer.json")
tcfg = json.load(open("artifacts/tokenizer_config.json"))
bos = tok.convert_tokens_to_ids(tcfg["bos_token"]); eos = tok.convert_tokens_to_ids(tcfg["eos_token"]); pad = tok.convert_tokens_to_ids(tcfg["pad_token"])

def fmt(ex):
    instr=(ex.get("instruction") or "").strip()
    inp=(ex.get("input") or "").strip()
    out=(ex.get("output") or "").strip()
    text = f"<|bos|>Instruction:\n{instr}\n\n" + (f"Input:\n{inp}\n\n" if inp else "") + f"Answer:\n{out}<|eos|>"
    ids = tok(text, add_special_tokens=False, truncation=True, max_length=128)["input_ids"]
    return {"ids": ids}

def main():
    ds = load_dataset("json", data_files="data/gen/instructions.jsonl")["train"].map(fmt, remove_columns=["instruction","input","output"])
    def collate(b):
        xs=[torch.tensor(x["ids"],dtype=torch.long) for x in b]
        x=torch.nn.utils.rnn.pad_sequence(xs, batch_first=True, padding_value=pad)
        return x, x.clone()
    dl = DataLoader(ds, batch_size=CFG["train"]["micro_bsz"], shuffle=True, collate_fn=collate)
    sd = torch.load("out/nova_seed/model.pt", map_location="cpu")
    m = NovaLM(NovaCfg(
        vocab_size=CFG["vocab_size"], max_seq_len=CFG["max_seq_len"], d_model=CFG["d_model"],
        n_heads=CFG["n_heads"], kv_heads=CFG["kv_heads"], n_layers=CFG["n_layers"],
        ffn_mult=CFG["ffn_mult"], dropout=CFG["dropout"], rope_base=CFG["rope_base"], moe_enabled=CFG["moe"]["enabled"], moe_experts=CFG["moe"]["experts"]
    ), grad_ckpt=CFG["train"]["grad_checkpoint"])
    m.load_state_dict(sd["model"], strict=False)
    dev="cuda" if torch.cuda.is_available() else "cpu"; m=m.to(dev).train()
    opt=AdamW(m.parameters(), lr=1.0e-4)
    steps=0; accum=CFG["train"]["grad_accum"]; warm=CFG["train"]["warmup_steps"]

    for epoch in range(1):
        for i,(x,y) in enumerate(dl):
            x=x.to(dev); y=y.to(dev)
            logits=m(x)
            loss=torch.nn.functional.cross_entropy(logits.view(-1,logits.size(-1)), y.view(-1), ignore_index=pad)
            loss.backward()
            if (i+1)%accum==0:
                if steps<warm:
                    for g in opt.param_groups: g["lr"]=1.0e-4*(steps+1)/max(1,warm)
                clip_grad_norm_(m.parameters(),1.0); opt.step(); opt.zero_grad(set_to_none=True)
            steps+=1
            _train_savepoint(steps, float(loss), {
                "phase": "sft",
                "lr": opt.param_groups[0]["lr"]
            })
            if steps%5==0: print(f"sft step {steps} loss={float(loss):.4f}")
            if steps>=20: break
        if steps>=20: break
    os.makedirs("out/nova_sft", exist_ok=True)
    torch.save({"model": m.state_dict(), "cfg": CFG}, "out/nova_sft/model.pt")
    print("✅ SFT saved -> out/nova_sft")
if __name__=="__main__": main()
