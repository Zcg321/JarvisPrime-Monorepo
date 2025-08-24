def source_weight(name:str)->float:
    return {"dfs":0.9,"traid":0.8,"tools":0.95,"web":0.85,"codegen":0.9}.get(name,0.8)

def affect_bias(msg:str)->float:
    m=(msg or "").lower(); marks=["stuck","frustrated","mad","angry","wtf","broken","not working"]
    return 1.15 if any(x in m for x in marks) else 1.0

def vote(proposals,last_user=""):
    bias=affect_bias(last_user); best=None; s=-1
    for p in proposals:
        w=p.get("weight",0.5)*source_weight(p.get("source","unknown"))*bias
        if w>s: s=w; best=p
    return best or {}

# --- Step B: ancestry hook ---
try:
    from jarvis_plugins.savepoint import SavepointLogger
    _SP = SavepointLogger()
except Exception:
    _SP = None

def _ancestry_log(event: str, payload: dict) -> None:
    if _SP:
        try:
            _SP.create({"event": event, **payload}, tag="reflex")
        except Exception:
            pass
# --- /ancestry hook ---
