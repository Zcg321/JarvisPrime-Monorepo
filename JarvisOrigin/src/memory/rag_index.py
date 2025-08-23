import os, glob
from sentence_transformers import SentenceTransformer
import faiss, numpy as np
class RAGIndex:
    def __init__(self,root="data/dna",model="sentence-transformers/all-MiniLM-L6-v2"):
        self.root=root; self.m=SentenceTransformer(model); self.docs=[]; self.index=None
    def _chunks(self,txt,sz=200,ov=40):
        i=0; n=len(txt)
        while i<n:
            yield txt[i:i+sz]; i+=max(1,sz-ov)
    def build(self):
        for p in glob.glob(os.path.join(self.root,"*")):
            try: t=open(p,"r",encoding="utf-8",errors="ignore").read()
            except: continue
            for c in self._chunks(t): self.docs.append((os.path.basename(p),c))
        if not self.docs: return
        X=self.m.encode([t for _,t in self.docs], convert_to_numpy=True); faiss.normalize_L2(X)
        self.index=faiss.IndexFlatIP(X.shape[1]); self.index.add(X.astype(np.float32))
    def search(self,q,k=4):
        if not self.index: return []
        x=self.m.encode([q], convert_to_numpy=True); faiss.normalize_L2(x)
        D,I=self.index.search(x.astype(np.float32),k)
        return [{"id":self.docs[i][0], "score":float(s), "text":self.docs[i][1]} for i,s in zip(I[0],D[0])]
