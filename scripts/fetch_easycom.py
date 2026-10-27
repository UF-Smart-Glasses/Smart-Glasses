import json, shutil
from pathlib import Path
from huggingface_hub import snapshot_download

REPO    = "Smart-Glasses/smart-glasses-eval"
FOLDER  = "sources/easycom/session_01"
ROOT    = Path(__file__).resolve().parents[1]
SIM_DIR = ROOT / "api/simulator_resources"

local = Path(snapshot_download(REPO, repo_type="dataset",
                               allow_patterns=[f"{FOLDER}/*"],
                               local_dir=Path.home() / "sg-data")) / FOLDER

def one(ext):
    files = list(local.glob(f"*{ext}"))
    if len(files) != 1:
        raise SystemExit(f"expected 1 {ext} in {local}, found {[f.name for f in files]}")
    return files[0]

shutil.copy(one(".mp4"), SIM_DIR / "easycom_gap.mp4")
shutil.copy(one(".wav"), SIM_DIR / "easycom_gap.wav")
shutil.copy(one(".npy"), ROOT / "database/sample_data/voice_Jack.npy")

cfg_path = SIM_DIR / "simulator_config.json"
cfg = json.loads(cfg_path.read_text())
cfg["target_video"] = "./api/simulator_resources/easycom_gap.mp4"
cfg["target_audio"] = "./api/simulator_resources/easycom_gap.wav"
cfg_path.write_text(json.dumps(cfg, indent=2) + "\n")

print("EasyCom session 1 ready. Run: python main.py, then python -m api.simulator")