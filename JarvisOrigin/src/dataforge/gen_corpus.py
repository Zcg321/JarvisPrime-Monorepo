import os, json, random
random.seed(7)
os.makedirs("data/gen", exist_ok=True)
OUT_TXT="data/gen/english_synth.txt"; OUT_INS="data/gen/instructions.jsonl"

subjects=["I","You","We","They","He","She","The system","Jarvis Prime","This engine","The model"]
verbs={"present":["build","analyze","question","guide","protect","reflect","optimize","compose","summarize","prioritize"],
       "past":["built","analyzed","questioned","guided","protected","reflected","optimized","composed","summarized","prioritized"],
       "future":["will build","will analyze","will question","will guide","will protect","will reflect","will optimize","will compose","will summarize","will prioritize"]}
objects=["the plan","a dataset","our approach","this request","the lineup","the strategy","memory anchors","reflex rules","a summary","risk mapping"]
adverbs=["carefully","boldly","ethically","precisely","reliably","transparently","patiently","recursively","deliberately"]
clauses=["when in doubt","under time pressure","after a failure","during review","before execution","when memory is thin","if risk is high","when funds are low","if clarity fades","after feedback"]

def gen_basic(n=200):
    out=[]
    for _ in range(n):
        s=random.choice(subjects); tense=random.choice(list(verbs.keys())); v=random.choice(verbs[tense])
        o=random.choice(objects); adv=random.choice(adverbs); cl=random.choice(clauses)
        out.append(random.choice([f"{s} {v} {o} {adv}.", f"{s} {v} {o}.", f"{s} {v} {o} {adv} {cl}."]))
    return out

intents=[("greet","Hello Jarvis, can you help me today?","Hello — yes. What do you need?"),
         ("summarize","Summarize: Profit is fuel, integrity is the path.","Summary: Profit is fuel; integrity is the path."),
         ("tool","Fetch ROI for DFS last week.","{\"tool\":\"dfs_roi\",\"args\":{\"range\":\"last_week\"}}"),
         ("reflex","I feel stuck.","Noted. Small step: define a win you can finish in 20 minutes, then act.")]

def gen_dialogs(n=100):
    out=[]
    for _ in range(n):
        k=random.choice(intents)
        if k[0]=="tool": out.append({"instruction":"Tool call","input":k[1],"output":k[2]})
        else: out.append({"instruction":k[0].capitalize(),"input":k[1],"output":k[2]})
    return out

etiquette=[{"instruction":"Tool JSON only","input":"Need market data fetch.","output":"{\"tool\":\"market_fetch\",\"args\":{\"symbol\":\"SPY\",\"interval\":\"1d\"}}"},
          {"instruction":"When NOT to call tool","input":"Reformat: 'profit can be pure' → title case.","output":"Profit Can Be Pure"},
          {"instruction":"RAG first","input":"What is SurgeCell allocation?","output":"DFS 30%, Voice Mirror 30%, Reflex 20%, Ghost 10%, TrAId 10%."},
          {"instruction":"Reflex self-check","input":"Decision chosen. Next?","output":"Check bankroll/safety, confirm tool necessity, prefer local memory; revise once if any fail."}]

def is_prime(n:int)->bool:
    if n<2: return False
    if n%2==0: return n==2
    r=int(n**0.5)
    for i in range(3,r+1,2):
        if n%i==0: return False
    return True

def gen_math(n=50):
    out=[]
    for _ in range(n):
        a=random.randint(2,999); b=random.randint(2,999)
        if random.random()<0.5: out.append({"instruction":"Add","input":f"{a}+{b}","output":str(a+b)})
        else: out.append({"instruction":"Prime?","input":str(a),"output":"yes" if is_prime(a) else "no"})
    return out

basic=gen_basic(200)
with open(OUT_TXT,"w",encoding="utf-8") as f: f.write("\n".join(basic))
inst=gen_dialogs(100)+etiquette+gen_math(50)
with open(OUT_INS,"w",encoding="utf-8") as f:
    for r in inst: f.write(json.dumps(r, ensure_ascii=False)+"\n")
print("✅ Synthetic corpus:", OUT_TXT, len(basic), "|", OUT_INS, len(inst))
