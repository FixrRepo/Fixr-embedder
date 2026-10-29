
import torch
import json
def serialize_tensor(tensor:torch.Tensor)->bytes:
    return json.dumps(tensor.detach().flatten().cpu().tolist())

def deserialize_tensor(data: bytes):
    return json.loads(data)