"""Modal app for the round-evals twin (twin/run_twin.py).

    modal run twin/modal_app.py --step download     # Qwen3.8-27B at Jinzhou's pinned revision, into the volume
    modal run twin/modal_app.py --step smoke        # a few rows per task, to check the setup
    modal run twin/modal_app.py --step full         # every arm and task
    cd twin/results && modal volume get --force constdrift-twin out .   # results back to this repo

One H200 with vLLM 0.30.0, the version and engine settings of his evaluations.
"""
import modal

MODEL_ID = "Qwen/Qwen3.8-27B"
REVISION = "1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0"   # the snapshot every round of his chain used
MODEL_DIR = f"/vol/models/Qwen3.8-27B-{REVISION[:8]}"

app = modal.App("constdrift-twin")
volume = modal.Volume.from_name("constdrift-twin", create_if_missing=True)
# vLLM 0.30.0 from PyPI, the version of his evaluations; it brings torch 2.13.0+cu130. The CUDA 13.0 devel base
# supplies nvcc, which FlashInfer needs to compile its kernels at startup (his pod image had the toolkit too).
# (The vllm/vllm-openai image has no Python Modal can detect, so it cannot host a Modal function.)
image = (
    modal.Image.from_registry("nvidia/cuda:13.0.2-devel-ubuntu24.04", add_python="3.12")
    .uv_pip_install("vllm==0.30.0", "huggingface_hub[hf_transfer]")
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
    .add_local_dir("twin/vendor/cse", "/root/cse")
    .add_local_dir("twin/arms", "/root/arms")
    .add_local_file("twin/run_twin.py", "/root/run_twin.py")
)
download_image = (modal.Image.debian_slim(python_version="3.12")
                  .uv_pip_install("huggingface_hub[hf_transfer]").env({"HF_HUB_ENABLE_HF_TRANSFER": "1"}))


@app.function(image=download_image, volumes={"/vol": volume}, timeout=3600, cpu=8, memory=32768)
def download():
    from huggingface_hub import snapshot_download

    snapshot_download(MODEL_ID, revision=REVISION, local_dir=MODEL_DIR)
    volume.commit()
    return MODEL_DIR


# Six hours caps the cost at about $33 (H200 $4.54/h plus CPU and memory).
@app.function(image=image, gpu="H200", volumes={"/vol": volume}, timeout=6 * 3600, cpu=8, memory=65536)
def evaluate(plan: str, limit: int = 0):
    import sys
    from pathlib import Path

    sys.path.insert(0, "/root")
    import run_twin

    out = Path("/vol/smoke" if plan == "smoke" else "/vol/out")
    run_twin.main(plan, MODEL_DIR, out, limit=limit, on_task_done=volume.commit)
    volume.commit()


@app.local_entrypoint()
def main(step: str = "smoke"):
    if step == "download":
        print(download.remote())
    elif step == "smoke":
        evaluate.remote("smoke", limit=16)
    elif step == "full":
        evaluate.remote("full")
    else:
        raise SystemExit(f"unknown step {step}")
