from jarvisprime.client import JarvisPrime

with JarvisPrime() as client:
    info = client.health()
    print("port", info.get("port"))
