# SETUP — Stage E execution guide for all 4 runners

This guide is intentionally explicit. Follow the section for your environment exactly; do not skip.

Runners and their assignments (from `configs/_index.json`):

| `runner_id`     | Hardware | Configs assigned | Queue time |
|---|---|---|---|
| `khanh_3070`    | Khanh's local RTX 3070, Windows + Py 3.13 | 4 SAM cells | ~6.92 h |
| `friend_3060`   | Friend's local RTX 3060 | 2 SAM-c10 + SGD/SWA fillers (5) | ~7.08 h |
| `khanh_colab`   | Khanh's Colab Pro (T4 baseline) | 4 SGD + 1 SWA-c10 | ~8.78 h |
| `friend_colab`  | Friend's Colab Pro (T4 baseline) | 2 SWA-c100 + 1 SWA-c10 + 1 SGD-c100 | ~7.20 h |

Each runner only ever writes to `results/runs_{runner_id}.jsonl`.

---

## A. Local Windows GPU (`khanh_3070`, `friend_3060`)

### A.1 Clone / pull the repo

```powershell
# First time:
git clone <repo-url> A2
cd A2

# Subsequent updates (do this before launching the queue):
git pull
```

### A.2 Python + venv

```powershell
# Inside the A2 directory
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

If `python` on your system is < 3.11 or > 3.13, install Python 3.12 first (most stable for the cu124 wheels).

### A.3 Install torch + torchvision with CUDA

```powershell
# CUDA 12.4 wheel (works on Ampere drivers >=550). For Python 3.13:
pip install --upgrade torch torchvision --index-url https://download.pytorch.org/whl/cu124

# If your driver is older and cu124 fails at runtime, try cu118:
# pip install --upgrade torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### A.4 Install remaining deps

```powershell
pip install -r requirements.txt
```

### A.5 Verify GPU is visible

```powershell
python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else None)"
```

Expected output:
```
2.5.x  True  NVIDIA GeForce RTX 3070  (or RTX 3060)
```

If `False`, do not proceed — `train.py` will hard-error on CPU. Re-check the cu124 install.

### A.6 Download CIFAR-10-C and CIFAR-100-C (one time, ~3 GB total)

```powershell
# CIFAR-10-C  (~2.7 GB)
curl -L -o CIFAR-10-C.tar  https://zenodo.org/record/2535967/files/CIFAR-10-C.tar
tar -xf CIFAR-10-C.tar -C data/

# CIFAR-100-C (~3 GB)
curl -L -o CIFAR-100-C.tar https://zenodo.org/record/3555552/files/CIFAR-100-C.tar
tar -xf CIFAR-100-C.tar -C data/
```

After extraction, verify:

```powershell
ls data/CIFAR-10-C/labels.npy
ls data/CIFAR-100-C/labels.npy
```

Both must exist.

### A.7 Generate configs

```powershell
python scripts/gen_configs.py
```

You should see 20 YAML files in `configs/` and `configs/_index.json`. Skip if already generated.

### A.8 Launch the queue

```powershell
# Khanh: runner_id is khanh_3070
python scripts/run_queue.py --runner-id khanh_3070

# Friend: runner_id is friend_3060
python scripts/run_queue.py --runner-id friend_3060
```

The script will:
- read `configs/_index.json` to find the configs assigned to your `runner_id`
- skip any whose `run_id` already appears in `results/runs_{runner_id}.jsonl`
- run them sequentially in priority order (longest first)
- write each completed result to `results/runs_{runner_id}.jsonl`
- record any failures in `results/failed_{runner_id}.jsonl` and continue

### A.9 Resume after a crash / restart

`train.py` automatically resumes from the latest periodic checkpoint
(`checkpoints/{run_id}_ep{N}.pt`, written every 25 epochs). If a config gets
interrupted mid-training, just re-run the queue:

```powershell
python scripts/run_queue.py --runner-id khanh_3070
```

It will skip already-completed configs and resume the interrupted one from
the latest periodic checkpoint.

To force a clean retrain of a specific config, delete its periodic checkpoints
first:

```powershell
del checkpoints\sam005_cifar100_s1_ep*.pt
python scripts/train.py --config configs/sam005_cifar100_s1.yaml --runner-id khanh_3070
```

### A.10 Send results back

After your queue completes:

```powershell
git add results/runs_khanh_3070.jsonl
git commit -m "results: khanh_3070 queue"
git push
```

(Or for `friend_3060` substitute `friend_3060`.)

Coordinate so the two PRs don't conflict — they shouldn't, because each runner
writes only to its own file.

---

## B. Colab Pro (`khanh_colab`, `friend_colab`)

See `docs/COLAB_RUNNER.md` for the Colab notebook template. Workflow summary:

1. Upload `data/CIFAR-10-C/` and `data/CIFAR-100-C/` to your Google Drive **once**
   (under `MyDrive/A2/data/`). Both runners' Colab share their own Drives, so
   each user does this for their own Colab.
2. Open the Colab notebook with cells from `docs/COLAB_RUNNER.md`.
3. Set `RUNNER_ID = "khanh_colab"` or `"friend_colab"` in the first cell.
4. Run all cells. The notebook clones the repo, mounts Drive, installs deps,
   and runs the queue.
5. After completion, the notebook pushes `results/runs_{runner_id}.jsonl` back
   to a branch on GitHub via the Colab terminal.

---

## C. Merging results (one person does this once, after all 4 queues finish)

```powershell
# Pull all 4 per-runner files (assuming they've been pushed to master)
git pull

# Verify all 4 files are present
ls results/runs_*.jsonl
# Expect: runs_khanh_3070.jsonl, runs_khanh_colab.jsonl, runs_friend_3060.jsonl, runs_friend_colab.jsonl

# Merge with strict validation (fails if any primary metric is null on a production row)
python scripts/merge_runs.py

# Output: results/runs.jsonl (canonical, sorted by run_id, deduplicated)

# Now generate the aggregated tables + figures for the paper
python scripts/aggregate.py
```

If `merge_runs.py` errors with missing primary metrics, the offending row
needs to be re-run (delete its checkpoints, re-run the queue on that runner).

---

## D. Common failure modes

| Symptom | Likely cause | Fix |
|---|---|---|
| `train.py` exits with `[error] No GPU detected` | cu124 wheel not installed correctly or torch version mismatch | Re-run §A.3, then `python -c "import torch; print(torch.cuda.is_available())"`. Should be `True`. |
| `FileNotFoundError: labels.npy not found` | CIFAR-C not extracted | Re-run §A.6 and verify `data/CIFAR-{10,100}-C/labels.npy` |
| Per-epoch time on 3070 > 20 s | num_workers low or AMP disabled | Confirm config has `use_amp: true`, `num_workers: 4`; check `torch.cuda.is_available()` |
| Colab cell disconnects mid-run | Idle timeout or runtime cap | `train.py` saves periodic checkpoints; just re-run the same Colab cell — it will resume |
| `merge_runs.py` says "duplicate run_id with disagreeing content" | Two runners ran the same config (shouldn't happen if `_index.json` is canonical) | Decide which result to keep; delete the row from the other's `runs_{runner_id}.jsonl` and re-merge |
| `merge_runs.py` says "missing primary metric" on a production row | CIFAR-C wasn't present when the run was eval'd, OR CKA failed silently | Delete that run's row from its `runs_{runner_id}.jsonl`, then re-run that config |

---

## E. Smoke-validation plan (before the main queue)

Both you and your friend should do this once on local hardware before
launching the full queue:

```powershell
# 1. Verify configs generated and indexed correctly
python scripts/gen_configs.py
python -c "import json; idx = json.load(open('configs/_index.json')); print(f'{idx[\"n_configs_total\"]} configs, longest queue {idx[\"longest_runner_wall_clock_h\"]} h')"

# 2. Dry-run the queue (no training; lists what would run)
python scripts/run_queue.py --runner-id khanh_3070 --dry-run

# 3. Smoke a single 10-epoch run (verify --runner-id routing + checkpoint + resume)
python scripts/train.py --config configs/swa_smoke.yaml --runner-id khanh_3070 --epochs 10 --allow-missing-metrics
# Expect one row appended to results/runs_khanh_3070.jsonl
# Verify: `tail -1 results/runs_khanh_3070.jsonl | python -m json.tool`

# 4. (Optional) Interrupt a smoke run mid-training (Ctrl-C after ~5 epochs)
python scripts/train.py --config configs/sgd_smoke.yaml --runner-id khanh_3070 --epochs 50 --allow-missing-metrics
# Wait until epoch 25 prints "[ckpt] saved sgd_smoke_s1_ep25.pt", then Ctrl-C
# Re-run:
python scripts/train.py --config configs/sgd_smoke.yaml --runner-id khanh_3070 --epochs 50 --allow-missing-metrics
# Should print "[resume] loading sgd_smoke_s1_ep25.pt" and continue
```

Only after smoke validation passes, launch the real queue (§A.8).
