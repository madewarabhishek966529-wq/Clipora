"""Hardware probe & adaptive Whisper model selector."""

import psutil
from typing import Tuple

def probe_hardware() -> dict:
    """Detect available CPU cores, RAM, and GPU/CUDA capabilities."""
    ram = psutil.virtual_memory()
    ram_gb = ram.total / (1024 ** 3)

    cuda_available = False
    cuda_vram_gb = 0.0
    device_name = "CPU"

    try:
        import torch
        if torch.cuda.is_available():
            cuda_available = True
            device_name = torch.cuda.get_device_name(0)
            cuda_vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
    except (ImportError, Exception):
        pass

    return {
        "ram_gb": round(ram_gb, 2),
        "cuda_available": cuda_available,
        "cuda_vram_gb": round(cuda_vram_gb, 2),
        "device_name": device_name,
        "cpu_count": psutil.cpu_count(logical=True) or 2,
    }

def pick_whisper_model() -> Tuple[str, str, str]:
    """Select optimal faster-whisper model, device, and compute_type based on available hardware.
    
    Returns:
        (model_size, device, compute_type)
    """
    hw = probe_hardware()
    if hw["cuda_available"]:
        vram = hw["cuda_vram_gb"]
        if vram >= 6.0:
            return "large-v3", "cuda", "float16"
        elif vram >= 3.0:
            return "medium", "cuda", "float16"
        else:
            return "small", "cuda", "float16"
    else:
        ram = hw["ram_gb"]
        if ram >= 16.0:
            return "medium", "cpu", "int8"
        elif ram >= 8.0:
            return "small", "cpu", "int8"
        else:
            return "base", "cpu", "int8"
