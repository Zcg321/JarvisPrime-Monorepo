import math, torch, torch.nn as nn, torch.nn.functional as F
from dataclasses import dataclass

class RMSNorm(nn.Module):
    def __init__(self, d, eps=1e-5): super().__init__(); self.eps=eps; self.w=nn.Parameter(torch.ones(d))
    def forward(self,x): return x*torch.rsqrt(x.pow(2).mean(-1,keepdim=True)+self.eps)*self.w

def rope(q,k,base=10000):
    B,H,T,D=q.shape; half=D//2; dev=q.device; dt=q.dtype
    freqs=1.0/(base**(torch.arange(half,device=dev,dtype=dt)/half))
    t=torch.arange(T,device=dev,dtype=dt); ang=torch.einsum('t,f->tf',t,freqs)
    ca,sa=torch.cos(ang)[None,None],torch.sin(ang)[None,None]
    def rot(x): x1,x2=x[...,:half],x[...,half:]; return torch.cat([x1*ca-x2*sa, x1*sa+x2*ca],-1)
    return rot(q), rot(k)

class SwiGLU(nn.Module):
    def __init__(self,d,mult=4.0,p=0.0):
        super().__init__()
        h=int(d*mult)
        self.w1=nn.Linear(d,h,bias=False)
        self.w2=nn.Linear(d,h,bias=False)
        self.w3=nn.Linear(h,d,bias=False)
        self.drop=nn.Dropout(p)
    def forward(self,x):
        return self.drop(self.w3(F.silu(self.w1(x))*self.w2(x)))

class Top2Gate(nn.Module):
    def __init__(self,d,n): super().__init__(); self.wg=nn.Linear(d,n,bias=False)
    def forward(self,x): return torch.topk(self.wg(x),k=2,dim=-1)

class MoE(nn.Module):
    def __init__(self,d,n=8,top_k=2,mult=4.0,p=0.0):
        super().__init__(); self.top_k=top_k; self.experts=nn.ModuleList([SwiGLU(d,mult,p) for _ in range(n)]); self.gate=Top2Gate(d,n)
    def forward(self,x):
        B,T,D=x.shape; vals,idx=self.gate(x); w=F.softmax(vals,dim=-1); y=torch.zeros_like(x)
        for k in range(self.top_k):
            eidx=idx[...,k]; wk=w[...,k]
            for e,exp in enumerate(self.experts):
                m=(eidx==e)
                if m.any():
                    xm = x[m]
                    y[m] += wk[m].unsqueeze(-1) * exp(xm)
        return y

class MQA(nn.Module):
    def __init__(self,d,heads,kv_heads=1,p=0.0,rope_base=10000):
        super().__init__(); assert d%heads==0; self.H=heads; self.D=d//heads; self.rope_base=rope_base
        self.q=nn.Linear(d,d,bias=False); self.k=nn.Linear(d,self.D*kv_heads,bias=False); self.v=nn.Linear(d,self.D*kv_heads,bias=False); self.o=nn.Linear(d,d,bias=False); self.drop=nn.Dropout(p)
    def forward(self,x,mask=None):
        B,T,Dm=x.shape; H=self.H; Dh=self.D
        q=self.q(x).view(B,T,H,Dh).transpose(1,2)
        k=self.k(x).view(B,T,1,Dh).transpose(1,2)
        v=self.v(x).view(B,T,1,Dh).transpose(1,2)
        q,k=rope(q,k,self.rope_base); k=k.expand(B,H,T,Dh); v=v.expand(B,H,T,Dh)
        att=(q@k.transpose(-1,-2))/math.sqrt(Dh)
        if mask is not None: att=att+mask
        y=(att.softmax(-1)@v).transpose(1,2).contiguous().view(B,T,Dm)
        return self.o(y)

class Block(nn.Module):
    def __init__(self,d,heads,kv_heads,mult,rope_base,use_moe,experts,p=0.0):
        super().__init__(); self.n1=RMSNorm(d); self.att=MQA(d,heads,kv_heads,p,rope_base); self.n2=RMSNorm(d); self.ff=MoE(d,experts,2,mult,p) if use_moe else SwiGLU(d,mult,p)
    def forward(self,x,mask=None): x=x+self.att(self.n1(x),mask); x=x+self.ff(self.n2(x)); return x

@dataclass
class NovaCfg:
    vocab_size:int=50000; max_seq_len:int=256; d_model:int=256; n_heads:int=8; kv_heads:int=1; n_layers:int=4; ffn_mult:float=4.0; dropout:float=0.0; rope_base:int=10000; moe_enabled:bool=True; moe_experts:int=4

class NovaLM(nn.Module):
    def __init__(self,cfg:NovaCfg,grad_ckpt=True):
        super().__init__(); self.cfg=cfg; self.emb=nn.Embedding(cfg.vocab_size,cfg.d_model)
        self.blocks=nn.ModuleList([Block(cfg.d_model,cfg.n_heads,cfg.kv_heads,cfg.ffn_mult,cfg.rope_base,use_moe=(cfg.moe_enabled and i%2==1),experts=cfg.moe_experts) for i in range(cfg.n_layers)])
        self.norm=RMSNorm(cfg.d_model); self.head=nn.Linear(cfg.d_model,cfg.vocab_size,bias=False); self.mask_cache=None; self.grad_ckpt=grad_ckpt
        for m in self.modules():
            if isinstance(m,(nn.Linear,nn.Embedding)): nn.init.normal_(m.weight, mean=0.0, std=0.02)
    def _mask(self,T,dev,dt):
        if self.mask_cache is not None and self.mask_cache.shape[-1]>=T: return self.mask_cache[:,:,:T,:T]
        m=torch.full((1,1,T,T), float("-inf"), device=dev, dtype=dt); self.mask_cache=torch.triu(m,1); return self.mask_cache
    def forward(self,idx):
        B,T=idx.shape; x=self.emb(idx); mask=self._mask(T,x.device,x.dtype)
        for blk in self.blocks:
            if self.training and self.grad_ckpt:
                x=torch.utils.checkpoint.checkpoint(lambda a: blk(a,mask), x, use_reentrant=False)
            else: x=blk(x,mask)
        return self.head(self.norm(x))
    @torch.no_grad()
    def generate(self,idx,max_new_tokens=256,top_p=0.9,temperature=0.8,eos_id=None):
        for _ in range(max_new_tokens):
            logits=self.forward(idx)[:,-1,:]/(temperature if temperature>0 else 1.0)
            probs=torch.softmax(logits,-1); sp,si=torch.sort(probs,descending=True); keep=(torch.cumsum(sp,-1)<=top_p); keep[...,0]=True
            sp=torch.where(keep,sp,torch.zeros_like(sp)); sp=sp/sp.sum(-1,keepdim=True)
            next_id=si.gather(-1, torch.multinomial(sp,1)); idx=torch.cat([idx,next_id],1)
            if eos_id is not None and int(next_id)==eos_id: break
        return idx
