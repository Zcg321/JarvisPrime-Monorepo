import os, sys
ROOT = os.path.abspath(os.path.dirname(__file__))
for rel in ["JarvisPrime","JarvisPrime/src","JarvisPrime/src.v2","JarvisPrime/src.v3","JarvisPrime/apps"]:
  p = os.path.join(ROOT, rel)
  if os.path.isdir(p) and p not in sys.path:
      sys.path.insert(0, p)
