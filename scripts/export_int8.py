try:
    import torch
    from JarvisOrigin.src.export.int8_export import dynamic_int8_export
    net = torch.nn.Sequential(torch.nn.Linear(16,16), torch.nn.ReLU(), torch.nn.Linear(16,16))
    print("INT8 export written to:", dynamic_int8_export(net, "artifacts/export/int8", {"note":"demo"}))
except ModuleNotFoundError:
    from JarvisOrigin.src.export.int8_export import dynamic_int8_export
    print("Torch missing; wrote meta only to:", dynamic_int8_export(None))
