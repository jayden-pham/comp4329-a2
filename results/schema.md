# `results/runs.jsonl` schema

Each line is a JSON object representing one completed training + evaluation run. Append-only; never edited in place. Each row is self-contained — readers should not need to join against other files to interpret it.

## Required fields

```json
{
  "run_id": "<unique string; e.g. 'sam005_cifar10_s1'>",
  "timestamp_utc": "<ISO 8601, e.g. '2026-05-22T03:14:11Z'>",
  "git_commit": "<short SHA of code at run time>",

  "config": {
    "optimizer": "sgd | sam | swa",
    "rho": 0.05,
    "swa_start_epoch": 100,
    "swa_lr": 0.05,
    "dataset": "cifar10 | cifar100",
    "model": "resnet18 | resnet50",
    "epochs": 200,
    "batch_size": 128,
    "lr": 0.1,
    "weight_decay": 5e-4,
    "momentum": 0.9,
    "augmentation": "standard | weak | strong",
    "seed": 1
  },

  "wall_clock_sec": 4123.5,
  "max_gpu_memory_mb": 6840,

  "metrics": {
    "id_accuracy": 0.9421,
    "id_loss": 0.2156,
    "id_ece": 0.0312,

    "ood_accuracy_avg": 0.7641,
    "ood_loss_avg": 0.8923,
    "ood_ece_avg": 0.0834,
    "ood_accuracy_per_corruption": {
      "gaussian_noise": [0.82, 0.74, 0.61, 0.49, 0.34],
      "shot_noise":     [0.83, 0.75, 0.62, 0.50, 0.35],
      "...":            "<one entry per corruption type, list of 5 severities>"
    },

    "sharpness_top_eig": 142.3,
    "sharpness_trace_estimate": 5840.1,
    "sharpness_sam_neighborhood_loss": 0.34,

    "paired_cka_penultimate": 0.812,
    "paired_cka_per_corruption": {
      "gaussian_noise": 0.79,
      "...": "<one entry per corruption type, averaged across severities>"
    },
    "paired_cka_per_layer": {
      "layer1": 0.91,
      "layer2": 0.88,
      "layer3": 0.83,
      "penultimate": 0.81
    }
  },

  "artifacts": {
    "checkpoint_path": "checkpoints/<run_id>.pt",
    "log_path": "logs/<run_id>.log"
  },

  "notes": "<free-form, e.g. 'restarted at epoch 87 after OOM; reduced batch to 96'>"
}
```

## Optional fields (write when applicable)

- `metrics.sharpness_top_eig_std` — standard deviation if estimated over multiple batches
- `metrics.calibration_ece_temperature_scaled` — if temperature scaling applied
- `metrics.feature_norm_id`, `metrics.feature_norm_ood` — feature L2 norms
- `config.swa_anneal_epochs` — if SWA schedule details matter

## Conventions

1. **Optimizer-distinct fields are still present in every row, with `null` when not applicable.** A SGD row has `"rho": null`, `"swa_start_epoch": null`, `"swa_lr": null`. This keeps downstream aggregation simple.
2. **`paired_cka_penultimate`** is computed as `1 / (N_corruptions * N_severities)` * sum over (corruption, severity) of `CKA(features(x_test_clean), features(corrupt(x_test_clean, corruption, severity)))`. The reduction order matters; `paired_cka_per_corruption` is averaged over severity, `paired_cka_penultimate` averages everything.
3. **Sharpness `top_eig`** is computed via power iteration (10 iterations) on the Hessian-vector product with a held-out batch of size 512. Repeat 3 times with different held-out batches; report the mean (and optionally std).
4. **All accuracies in [0, 1].**
5. **ECE** computed with 15 equal-mass bins (Naeini 2015 / Guo et al. 2017 convention).
6. **One row per completed run.** No partial rows. If a run dies, leave a `failed_runs.jsonl` entry instead.

## Aggregation

`scripts/aggregate.py` (written in Stage D) reads this file and produces:
- `results/tables/main_grid.tex` — optimizer × dataset main results
- `results/tables/per_corruption.tex` — per-corruption breakdown
- `results/figures/scatter_sharpness_vs_ood.pdf`
- `results/figures/scatter_cka_vs_ood.pdf`
- `results/figures/per_corruption_bars.pdf`

The aggregator computes mean ± seed-std for each (optimizer, dataset) cell, and partial correlation across all rows.
