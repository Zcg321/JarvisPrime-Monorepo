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
from datasets import Dataset
from torch.utils.data import DataLoader
from torch.nn.utils import clip_grad_norm_
from torch.optim import AdamW
from transformers import PreTrainedTokenizerFast
import yaml
from src.core.model import NovaLM, NovaCfg

CFG = yaml.safe_load(open("configs/nova_1p3b.yaml"))
tok = PreTrainedTokenizerFast(tokenizer_file="artifacts/tokenizer.json")
tcfg = json.load(open("artifacts/tokenizer_config.json"))
bos = tok.convert_tokens_to_ids(tcfg["bos_token"]); eos = tok.convert_tokens_to_ids(tcfg["eos_token"]); pad = tok.convert_tokens_to_ids(tcfg["pad_token"])

def collect():
    files=[]
    for root,_,fs in os.walk("data"):
        for f in fs:
            if f.endswith((".txt",".md",".json",".jsonl",".py",".yml",".yaml")):
                files.append(os.path.join(root,f))
    texts=[]
    for p in files:
        try: texts.append(open(p,"r",encoding="utf-8",errors="ignore").read())
        except: pass
    if not texts: raise SystemExit("No training texts. Run `make synth` or add corpus.")
    return texts

def build_dataset(block=128):
    texts = collect()
    ids=[]
    for t in texts:
        enc = tok(t, add_special_tokens=False)["input_ids"]
        if enc: ids += [bos] + enc + [eos]
    chunks=[ids[i:i+block] for i in range(0, max(0,len(ids)-block), block)]
    if not chunks: raise SystemExit("Corpus too small for chosen block size.")
    return Dataset.from_dict({"input_ids":chunks})

def collate(batch):
    xs=[torch.tensor(b["input_ids"], dtype=torch.long) for b in batch]
    x=torch.stack(xs,0); y=x.clone()
    return x,y

def try_deepspeed():
    try:
        import deepspeed
        return deepspeed
    except Exception:
        return None

def main():
    device="cuda" if torch.cuda.is_available() else "cpu"
    ds = build_dataset(block=CFG["train"]["block_size"])
    dl = DataLoader(ds,batch_size=CFG["train"]["micro_bsz"],shuffle=True,drop_last=True,collate_fn=collate)
    model = NovaLM(NovaCfg(
        vocab_size=CFG["vocab_size"], max_seq_len=CFG["max_seq_len"], d_model=CFG["d_model"],
        n_heads=CFG["n_heads"], kv_heads=CFG["kv_heads"], n_layers=CFG["n_layers"],
        ffn_mult=CFG["ffn_mult"], dropout=CFG["dropout"], rope_base=CFG["rope_base"], moe_enabled=CFG["moe"]["enabled"], moe_experts=CFG["moe"]["experts"]
    ), grad_ckpt=CFG["train"]["grad_checkpoint"])
    model = model.to(device)

    ds_mod = try_deepspeed()
    if ds_mod:
        engine, optimizer, _, _ = ds_mod.initialize(
            model=model, model_parameters=model.parameters(),
            config="configs/deepspeed_zero2.json", optimizer=AdamW(model.parameters(), lr=CFG["train"]["lr"])
        )
        runner=("ds",engine); module=lambda: runner[1].module
    else:
        opt=AdamW(model.parameters(), lr=CFG["train"]["lr"])
        runner=("vanilla",(model,opt)); module=lambda: runner[1][0]

    steps=0; warm=CFG["train"]["warmup_steps"]; accum=CFG["train"]["grad_accum"]; save_every=CFG.get("save_every_steps",50)
    print("✅ pretrain starting…")
    for ep in range(CFG["train"]["epochs"]):
        for i,(x,y) in enumerate(dl):
            x=x.to(device); y=y.to(device)
            if runner[0]=="ds":
                eng=runner[1]; logits=eng(x)
                loss=torch.nn.functional.cross_entropy(logits.view(-1, logits.size(-1)), y.view(-1), ignore_index=pad)
                eng.backward(loss)
                if (i+1)%accum==0: eng.step(); eng.zero_grad()
            else:
                m,opt=runner[1]; logits=m(x)
                loss=torch.nn.functional.cross_entropy(logits.view(-1, logits.size(-1)), y.view(-1), ignore_index=pad)
                loss.backward()
                if (i+1)%accum==0:
                    if steps<warm:
                        for g in opt.param_groups: g["lr"]=CFG["train"]["lr"]*(steps+1)/max(1,warm)
                    clip_grad_norm_(m.parameters(),1.0); opt.step(); opt.zero_grad(set_to_none=True)
            steps+=1
            _train_savepoint(steps, float(loss), {
                "phase": "pretrain",
                "lr": (runner[1][1].param_groups[0]["lr"] if runner[0]=="vanilla" else CFG["train"]["lr"])
            })
            if steps%1==0: print(f"step {steps} loss={float(loss):.4f}")
            if steps%save_every==0:
                os.makedirs("out/nova_ckpt", exist_ok=True)
                torch.save({"model": module().state_dict(), "cfg": CFG}, f"out/nova_ckpt/step_{steps}.pt")
            if steps>=20: break
        if steps>=20: break
    os.makedirs("out/nova_seed", exist_ok=True)
    torch.save({"model": module().state_dict(), "cfg": CFG}, "out/nova_seed/model.pt")
    tok.save_pretrained("out/nova_seed")
    print("✅ saved -> out/nova_seed")
if __name__=="__main__": main()
