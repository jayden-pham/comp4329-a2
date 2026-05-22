# COLAB_RUNNER.md — Colab Pro execution template

Paste the cells below into a fresh Colab notebook in order. **Only change `RUNNER_ID`** at the top — everything else runs unchanged.

The notebook:
1. Sets your runner_id and your GitHub repo URL.
2. Mounts your Google Drive.
3. Clones the repo to `/content/A2`.
4. Symlinks `data/` and `results/` to Drive so CIFAR-C and result files persist across runtime disconnects.
5. Installs pip dependencies (torch is already in Colab).
6. Verifies GPU access.
7. Runs the queue for your runner_id.
8. Pushes the results back to a branch on GitHub.

---

## Cell 1 — configuration (ONLY EDIT THIS CELL)

```python
# Set these once:
RUNNER_ID = "khanh_colab"       # "khanh_colab" or "friend_colab"
GIT_REPO_URL = "https://github.com/<YOUR_GH_USERNAME>/<YOUR_REPO_NAME>.git"
GIT_BRANCH_FOR_RESULTS = f"runs/{RUNNER_ID}"

# Path on Google Drive where CIFAR-10-C and CIFAR-100-C are pre-uploaded.
# Both must exist as data/CIFAR-10-C/labels.npy and data/CIFAR-100-C/labels.npy.
DRIVE_DATA_PATH = "/content/drive/MyDrive/A2/data"
DRIVE_RESULTS_PATH = "/content/drive/MyDrive/A2/results"
DRIVE_CHECKPOINTS_PATH = "/content/drive/MyDrive/A2/checkpoints"
```

## Cell 2 — mount Drive

```python
from google.colab import drive
drive.mount("/content/drive")
```

## Cell 3 — verify CIFAR-C is on Drive

```python
import os
for p in [f"{DRIVE_DATA_PATH}/CIFAR-10-C/labels.npy",
          f"{DRIVE_DATA_PATH}/CIFAR-100-C/labels.npy"]:
    assert os.path.exists(p), f"Missing: {p}. Upload CIFAR-C to {DRIVE_DATA_PATH} first."
print("CIFAR-C present on Drive")

# Ensure the persistent dirs exist
os.makedirs(DRIVE_RESULTS_PATH, exist_ok=True)
os.makedirs(DRIVE_CHECKPOINTS_PATH, exist_ok=True)
```

## Cell 4 — clone the repo

```python
import os, shutil
if os.path.exists("/content/A2"):
    shutil.rmtree("/content/A2")
!git clone {GIT_REPO_URL} /content/A2
%cd /content/A2
!git pull
```

## Cell 5 — link Drive paths into the repo

```python
%cd /content/A2
# data/ -> Drive (read-only is fine)
!rm -rf data && ln -s {DRIVE_DATA_PATH} data

# results/ -> Drive (so partial results survive disconnects)
!rm -rf results && mkdir -p {DRIVE_RESULTS_PATH} && ln -s {DRIVE_RESULTS_PATH} results

# checkpoints/ -> Drive (so resume works across disconnects)
!rm -rf checkpoints && mkdir -p {DRIVE_CHECKPOINTS_PATH} && ln -s {DRIVE_CHECKPOINTS_PATH} checkpoints

!ls -la data results checkpoints
```

## Cell 6 — install Python deps (torch is already in Colab)

```python
!pip -q install pyyaml pymupdf requests
# matplotlib + numpy are already in Colab
```

## Cell 7 — verify GPU

```python
import torch
print("torch:", torch.__version__, "| CUDA available:", torch.cuda.is_available(),
      "| device:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "(no GPU)")
assert torch.cuda.is_available(), "No GPU runtime. Switch to GPU in Runtime → Change runtime type."
```

## Cell 8 — generate configs (idempotent; safe to re-run)

```python
%cd /content/A2
!python scripts/gen_configs.py
```

## Cell 9 — dry-run the queue (sanity check before training)

```python
!python scripts/run_queue.py --runner-id {RUNNER_ID} --dry-run
```

Inspect the output — it should list the configs assigned to your `RUNNER_ID` in priority order.

## Cell 10 — run the queue

```python
!python scripts/run_queue.py --runner-id {RUNNER_ID}
```

This is the long-running cell. Expect ~8 h for `khanh_colab`, ~7 h for `friend_colab`.

If the Colab runtime disconnects mid-run:
1. Reconnect and re-run cells 4–10. The data and results are on Drive, so nothing is lost.
2. `train.py` auto-resumes from the latest periodic checkpoint (every 25 epochs).
3. `run_queue.py` skips already-completed configs.

## Cell 11 — push results back to GitHub

```python
%cd /content/A2

# GitHub auth: use a Personal Access Token in your repo's Settings → Developer settings
# Or set up an SSH key in Colab. Easiest is to embed the token here:
GIT_USER  = "your-github-username"
GIT_EMAIL = "your-github-email@example.com"
GH_TOKEN  = "ghp_xxxxxxxxxxxxxxxxxxxx"   # one-shot; do not commit

!git config user.name  "{GIT_USER}"
!git config user.email "{GIT_EMAIL}"
!git remote set-url origin https://{GIT_USER}:{GH_TOKEN}@github.com/{GIT_USER}/{GIT_REPO_URL.split('/')[-1]}

# Branch + commit
!git checkout -B {GIT_BRANCH_FOR_RESULTS}
!git add results/runs_{RUNNER_ID}.jsonl
!git commit -m "results: {RUNNER_ID} queue complete"
!git push -u origin {GIT_BRANCH_FOR_RESULTS}
```

After this cell completes, open a PR from `runs/{RUNNER_ID}` to `master` on GitHub.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `assert torch.cuda.is_available()` fails in cell 7 | Runtime → Change runtime type → GPU (T4 minimum). Re-run from cell 2. |
| `Missing: .../labels.npy` in cell 3 | Upload CIFAR-10-C and CIFAR-100-C to your Drive under `MyDrive/A2/data/` (one-time, ~3 GB). Local files won't work — they don't persist. |
| Cell 10 runs but very slow (>30 min per SGD epoch) | Confirm Cell 7 reported a GPU (not "no GPU"). Check `nvidia-smi` in a new cell. |
| `git push` rejected in cell 11 | Your token may not have `repo` scope. Regenerate at github.com/settings/tokens with `repo` permission. |
| Runtime disconnects every ~12 h | Expected on Colab Pro; resume is automatic — just re-run cells 4–10. |
| OOM on a small Colab GPU | Lower `batch_size` to 64 in the config (1-line edit), re-run. The rest of the pipeline is unaffected. |
