"""
Compare training results across experiment runs.

Scans models/ for training_log.json files from onepiece and aot experiments,
then produces:
  1. Console table: formatted comparison with GAN improvement summary
  2. JSON report: structured metrics in models/comparison_report.json
  3. Optional plot: training curves saved as PNG (requires matplotlib)

Usage:
    cd ai_engine
    python -m scripts.compare
    python -m scripts.compare --models-dir models/ --plot
"""

import argparse
import json
from pathlib import Path

# ── Path defaults (relative to this script) ─────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
AI_ENGINE_DIR = SCRIPT_DIR.parent
DEFAULT_MODELS_DIR = AI_ENGINE_DIR / "models"
DEFAULT_OUTPUT = AI_ENGINE_DIR / "models" / "comparison_report.json"

DATASET_PREFIXES = ("onepiece", "aot")


# ═══════════════════════════════════════════════════════════════════════════
# Discovery
# ═══════════════════════════════════════════════════════════════════════════

def find_experiments(models_dir: Path) -> list[dict]:
    """Scan models/ for onepiece*/ aot*/ dirs containing training_log.json.

    Supports two layouts:
      Flat:    models/onepiece-baseline/training_log.json
      Nested:  models/onepiece/baseline/training_log.json
    """
    experiments: list[dict] = []
    if not models_dir.exists():
        return experiments

    for entry in sorted(models_dir.iterdir()):
        if not entry.is_dir():
            continue

        name_lower = entry.name.lower()
        matched_prefix = None
        for prefix in DATASET_PREFIXES:
            if name_lower.startswith(prefix):
                matched_prefix = prefix
                break

        if matched_prefix is None:
            continue

        log_path = entry / "training_log.json"

        if log_path.exists():
            # ── Flat layout ──
            run_name = _derive_run_name(entry.name, matched_prefix)
            exp = _load_log(log_path, matched_prefix, run_name)
            if exp is not None:
                experiments.append(exp)
            continue  # don't descend into flat dirs

        # ── Nested layout: scan subdirectories ──
        for subdir in sorted(entry.iterdir()):
            if not subdir.is_dir():
                continue
            sub_log = subdir / "training_log.json"
            if sub_log.exists():
                exp = _load_log(sub_log, matched_prefix, subdir.name)
                if exp is not None:
                    experiments.append(exp)

    return experiments


def _derive_run_name(dir_name: str, prefix: str) -> str:
    """Extract run label from directory name.

    Examples:
        onepiece-baseline  → baseline
        onepiece-gan       → gan
        onepiece-gan-run   → gan-run
        onepiece           → baseline  (default guess)
    """
    remaining = dir_name[len(prefix):]
    # Strip leading separator
    if remaining and remaining[0] in ("-", "_"):
        remaining = remaining[1:]
    return remaining if remaining else "baseline"


# ═══════════════════════════════════════════════════════════════════════════
# Loading
# ═══════════════════════════════════════════════════════════════════════════

def _load_log(log_path: Path, dataset: str, run_name: str) -> dict | None:
    """Load a training_log.json and extract summary metrics.

    Returns dict with extracted fields, or None on error / empty data.
    """
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"  [WARN] Could not read {log_path}: {exc}")
        return None

    config = data.get("config", {})
    val_acc_list = data.get("val_acc", [])
    train_acc_list = data.get("train_acc", [])
    val_loss_list = data.get("val_loss", [])

    if not val_acc_list:
        print(f"  [WARN] No validation metrics in {log_path}")
        return None

    # Best epoch (1-indexed)
    best_val = max(val_acc_list)
    best_epoch = val_acc_list.index(best_val) + 1
    best_train_at_val = (
        train_acc_list[best_epoch - 1] if len(train_acc_list) >= best_epoch
        else train_acc_list[-1]
    )

    # Final metrics
    final_train = train_acc_list[-1] if train_acc_list else 0.0
    final_val = val_acc_list[-1]

    # GAP: train acc − best val acc (generalisation gap)
    gap = final_train - best_val

    # Prefer config.dataset as canonical name (handles flat layout correctly)
    canonical_dataset = config.get("dataset", dataset)

    return {
        "dataset": canonical_dataset,
        "run": run_name,
        "use_gan": config.get("use_gan", False),
        "best_val_acc": best_val,
        "best_epoch": best_epoch,
        "best_train_acc": best_train_at_val,
        "final_train_acc": final_train,
        "final_val_acc": final_val,
        "final_train_loss": round(train_acc_list[-1], 4) if train_acc_list else 0.0,
        "final_val_loss": round(val_loss_list[-1], 4) if val_loss_list else 0.0,
        "gap": round(gap, 2),
        "epochs_trained": len(val_acc_list),
        "total_train": config.get("total_train", 0),
        "num_classes": config.get("num_classes", 0),
        "config": config,
        "log_path": str(log_path),
    }


# ═══════════════════════════════════════════════════════════════════════════
# Console output
# ═══════════════════════════════════════════════════════════════════════════

def print_table(experiments: list[dict]) -> None:
    """Print formatted comparison table with GAN improvement summary."""
    if not experiments:
        _print_no_experiments()
        return

    # Stable sort: onepiece before aot, baseline before gan
    experiments.sort(key=_sort_key)

    print()
    print("Experiment Comparison")
    print("=" * 83)
    header = (
        f"{'Dataset':<10} | {'Run':<10} | {'Best Val Acc':>12} | "
        f"{'Best Epoch':>11} | {'Final Train Acc':>15} | {'GAP Δ':>9}"
    )
    print(header)
    print("-" * len(header))

    for exp in experiments:
        gap_sign = "+" if exp["gap"] > 0 else ""
        print(
            f"{exp['dataset']:<10} | "
            f"{exp['run']:<10} | "
            f"{exp['best_val_acc']:>8.2f}%    | "
            f"{exp['best_epoch']:>7}     | "
            f"{exp['final_train_acc']:>11.2f}%     | "
            f"{gap_sign}{exp['gap']:>5.2f}%"
        )

    _print_gan_improvement(experiments)
    print(f"\nTotal experiments: {len(experiments)}")


def _sort_key(exp: dict) -> tuple:
    """Sort: dataset order, then baseline before GAN runs."""
    ds_order = {p: i for i, p in enumerate(DATASET_PREFIXES)}
    ds_rank = ds_order.get(exp["dataset"], 99)
    # baseline < gan-run < gan
    run_name = exp["run"].lower()
    if "baseline" in run_name:
        run_rank = 0
    elif "gan" in run_name:
        run_rank = 1
    else:
        run_rank = 2
    return (ds_rank, run_rank, exp["run"])


def _print_no_experiments() -> None:
    """Print helpful message when no training logs are found."""
    print()
    print("  No training_log.json files found.")
    print(f"  Scanned: {DEFAULT_MODELS_DIR}")
    print()
    print("  Expected structure (flat):")
    print(f"    {DEFAULT_MODELS_DIR}/onepiece-baseline/training_log.json")
    print(f"    {DEFAULT_MODELS_DIR}/onepiece-gan/training_log.json")
    print(f"    {DEFAULT_MODELS_DIR}/aot-baseline/training_log.json")
    print(f"    {DEFAULT_MODELS_DIR}/aot-gan/training_log.json")
    print()
    print("  Expected structure (nested):")
    print(f"    {DEFAULT_MODELS_DIR}/onepiece/baseline/training_log.json")
    print(f"    {DEFAULT_MODELS_DIR}/onepiece/gan-run/training_log.json")
    print(f"    {DEFAULT_MODELS_DIR}/aot/baseline/training_log.json")
    print(f"    {DEFAULT_MODELS_DIR}/aot/gan-run/training_log.json")


def _print_gan_improvement(experiments: list[dict]) -> None:
    """Print per-dataset GAN improvement if baseline + GAN pair exists."""
    by_dataset: dict[str, dict[str, dict]] = {}
    for exp in experiments:
        ds = exp["dataset"]
        run_label = _normalise_run_label(exp["run"])
        by_dataset.setdefault(ds, {})[run_label] = exp

    improvements: list[str] = []
    for ds_name in DATASET_PREFIXES:
        runs = by_dataset.get(ds_name, {})
        baseline = runs.get("baseline")
        gan = runs.get("gan")
        if baseline and gan:
            delta = gan["best_val_acc"] - baseline["best_val_acc"]
            improvements.append(f"  {ds_name.capitalize():<11} {delta:+.2f}%")

    if improvements:
        print()
        print("GAN Improvement (Best Val Acc):")
        for line in improvements:
            print(line)


def _normalise_run_label(name: str) -> str:
    """Map run labels to canonical 'baseline' / 'gan' for pairing."""
    lower = name.lower()
    if "baseline" in lower:
        return "baseline"
    if "gan" in lower:
        return "gan"
    return lower


# ═══════════════════════════════════════════════════════════════════════════
# Config traceability (dataset.csv style)
# ═══════════════════════════════════════════════════════════════════════════

CONFIG_KEYS = [
    "architecture", "dataset", "num_classes", "total_train",
    "use_gan", "batch_size", "epochs_trained",
    "lr", "weight_decay", "label_smoothing",
]


def print_config_csv(experiments: list[dict]) -> None:
    """Print training config summary for traceability."""
    if not experiments:
        return

    print()
    print("=" * 120)
    print("Training Config Traceability")
    print("=" * 120)

    # Header
    header = f"{'Dataset':<10} | {'Run':<10} | " + " | ".join(
        f"{k:<16}" for k in CONFIG_KEYS
    )
    print(header)
    print("-" * len(header))

    for exp in experiments:
        cfg = exp["config"]
        values: list[str] = []
        for key in CONFIG_KEYS:
            val = cfg.get(key, "")
            values.append(_fmt_config_value(val))
        print(f"{exp['dataset']:<10} | {exp['run']:<10} | " + " | ".join(values))


def _fmt_config_value(val) -> str:
    """Format a config value for fixed-width display."""
    if val is None:
        return f"{'N/A':<16}"
    if isinstance(val, bool):
        return f"{str(val):<16}"
    if isinstance(val, float):
        if abs(val) < 1e-5:
            return f"{val:<16.2e}"
        if abs(val) < 0.001:
            return f"{val:<16.6f}"
        return f"{val:<16.4f}"
    return f"{str(val):<16}"


# ═══════════════════════════════════════════════════════════════════════════
# JSON report
# ═══════════════════════════════════════════════════════════════════════════

def save_report(experiments: list[dict], output_path: Path) -> None:
    """Save structured comparison_report.json with all extracted metrics."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # ── Per-experiment summary ──
    summary: list[dict] = []
    for exp in experiments:
        summary.append({
            "dataset": exp["dataset"],
            "run": exp["run"],
            "use_gan": exp["use_gan"],
            "best_val_acc": exp["best_val_acc"],
            "best_epoch": exp["best_epoch"],
            "best_train_acc": exp["best_train_acc"],
            "final_train_acc": exp["final_train_acc"],
            "final_val_acc": exp["final_val_acc"],
            "final_train_loss": exp["final_train_loss"],
            "final_val_loss": exp["final_val_loss"],
            "gap_train_val": exp["gap"],
            "epochs_trained": exp["epochs_trained"],
            "total_train": exp["total_train"],
            "num_classes": exp["num_classes"],
        })

    # ── GAN improvement per dataset ──
    gan_improvements: dict = {}
    by_dataset: dict[str, dict[str, dict]] = {}
    for exp in experiments:
        by_dataset.setdefault(exp["dataset"], {})[
            _normalise_run_label(exp["run"])
        ] = exp

    for ds_name, runs in by_dataset.items():
        baseline = runs.get("baseline")
        gan = runs.get("gan")
        if baseline and gan:
            gan_improvements[ds_name] = {
                "baseline_best_val_acc": baseline["best_val_acc"],
                "gan_best_val_acc": gan["best_val_acc"],
                "improvement": round(
                    gan["best_val_acc"] - baseline["best_val_acc"], 2
                ),
            }

    # ── Full config snapshot for traceability ──
    config_snapshot: list[dict] = []
    for exp in experiments:
        config_snapshot.append({
            "dataset": exp["dataset"],
            "run": exp["run"],
            "log_path": exp["log_path"],
            "config": exp["config"],
        })

    report = {
        "generated_by": "scripts/compare.py",
        "num_experiments": len(experiments),
        "experiments": summary,
        "gan_improvements": gan_improvements,
        "config_snapshot": config_snapshot,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"Report saved → {output_path}")


# ═══════════════════════════════════════════════════════════════════════════
# Optional plot (matplotlib)
# ═══════════════════════════════════════════════════════════════════════════

def generate_plot(experiments: list[dict], output_dir: Path) -> None:
    """Generate training curve plots (matplotlib is optional)."""
    try:
        import matplotlib
        matplotlib.use("Agg")  # non-interactive backend
        import matplotlib.pyplot as plt
    except ImportError:
        print("\n  [INFO] matplotlib not installed. Skipping plot generation.")
        print("         Install with: pip install matplotlib")
        return

    if not experiments:
        return

    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
              "#9467bd", "#8c564b", "#e377c2", "#7f7f7f"]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Training Curves Comparison", fontsize=14, fontweight="bold")

    for i, exp in enumerate(experiments):
        try:
            with open(exp["log_path"], "r", encoding="utf-8") as f:
                full_data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        epochs = list(range(1, len(full_data.get("val_acc", [])) + 1))
        if not epochs:
            continue

        color = colors[i % len(colors)]
        label = f"{exp['dataset']}/{exp['run']}"

        # Top-left: Training Accuracy
        train_acc = full_data.get("train_acc", [])
        if train_acc:
            axes[0, 0].plot(epochs, train_acc, color=color, linewidth=1.5,
                            label=label, alpha=0.85)
        axes[0, 0].set_title("Training Accuracy")
        axes[0, 0].set_xlabel("Epoch")
        axes[0, 0].set_ylabel("Accuracy (%)")
        axes[0, 0].legend(fontsize=7, loc="lower right")
        axes[0, 0].grid(True, alpha=0.3)

        # Top-right: Validation Accuracy
        val_acc = full_data.get("val_acc", [])
        if val_acc:
            axes[0, 1].plot(epochs, val_acc, color=color, linewidth=1.5,
                            label=label, alpha=0.85)
        axes[0, 1].set_title("Validation Accuracy")
        axes[0, 1].set_xlabel("Epoch")
        axes[0, 1].set_ylabel("Accuracy (%)")
        axes[0, 1].legend(fontsize=7, loc="lower right")
        axes[0, 1].grid(True, alpha=0.3)

        # Bottom-left: Training Loss
        train_loss = full_data.get("train_loss", [])
        if train_loss:
            axes[1, 0].plot(epochs, train_loss, color=color, linewidth=1.5,
                            label=label, alpha=0.85)
        axes[1, 0].set_title("Training Loss")
        axes[1, 0].set_xlabel("Epoch")
        axes[1, 0].set_ylabel("Loss")
        axes[1, 0].legend(fontsize=7, loc="upper right")
        axes[1, 0].grid(True, alpha=0.3)

        # Bottom-right: Validation Loss
        val_loss = full_data.get("val_loss", [])
        if val_loss:
            axes[1, 1].plot(epochs, val_loss, color=color, linewidth=1.5,
                            label=label, alpha=0.85)
        axes[1, 1].set_title("Validation Loss")
        axes[1, 1].set_xlabel("Epoch")
        axes[1, 1].set_ylabel("Loss")
        axes[1, 1].legend(fontsize=7, loc="upper right")
        axes[1, 1].grid(True, alpha=0.3)

    plt.tight_layout()
    plot_path = output_dir / "comparison_curves.png"
    fig.savefig(plot_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Plot saved   → {plot_path}")


# ═══════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare training results across experiment runs"
    )
    parser.add_argument(
        "--models-dir",
        type=Path,
        default=DEFAULT_MODELS_DIR,
        help=f"Path to models/ directory (default: {DEFAULT_MODELS_DIR})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Path for JSON report (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Save training curve plots as PNG (requires matplotlib)",
    )
    args = parser.parse_args()

    models_dir: Path = args.models_dir
    output_path: Path = args.output

    print(f"Scanning: {models_dir}")

    # ── Discover ──
    experiments = find_experiments(models_dir)

    if not experiments:
        _print_no_experiments()
        return

    print(f"  Found {len(experiments)} experiment(s)")

    # ── Console outputs ──
    print_table(experiments)
    print_config_csv(experiments)

    # ── File outputs ──
    save_report(experiments, output_path)

    if args.plot:
        generate_plot(experiments, models_dir)


if __name__ == "__main__":
    main()
