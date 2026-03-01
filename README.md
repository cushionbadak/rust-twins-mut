# rust-twins-mut

LLM-based Rust code mutator from the [Rust-twins](https://dl.acm.org/doi/10.1145/3691620.3695059) paper, using [GPT-OSS-20B](https://console.cloud.google.com/vertex-ai/model-garden) on Google Cloud Vertex AI.

The authors state that their implementation and data are publicly available (at [project page](https://sites.google.com/view/rust-twins/index) and [anonymous repo](https://anonymous.4open.science/r/Rust-twins-481C/README.md)), but the repository itself is almost unusable, so this repository is a clean reimplementation.

## Quick Setup (Ubuntu)

On a bare Ubuntu machine, run the setup script — it installs everything (gcloud CLI, uv, dependencies) and walks you through Google Cloud authentication:

```bash
git clone --recurse-submodules https://github.com/cushionbadak/rust-twins-mut.git
cd rust-twins-mut
./setup.sh                  # opens browser for Google login
./setup.sh --no-browser     # headless: prints a URL to auth from another machine
```

Then edit `gpt-oss-20b-google-cloud-call/config.py` to set your GCP project ID, and enable the GPT-OSS API in [Model Garden](https://console.cloud.google.com/vertex-ai/model-garden).

## Manual Setup

Prerequisites: Python 3.10+, [Google Cloud SDK](https://cloud.google.com/sdk/docs/install), [uv](https://github.com/astral-sh/uv).

```bash
git clone --recurse-submodules https://github.com/cushionbadak/rust-twins-mut.git
cd rust-twins-mut

gcloud init
gcloud auth application-default login

# Edit gpt-oss-20b-google-cloud-call/config.py and set project_id

uv sync
```

If you already cloned without `--recurse-submodules`:

```bash
git submodule update --init --recursive
```

## Usage

```bash
# Basic usage — mutate Rust files in a folder
uv run python -m rust_twins_mut ./seeds

# Custom settings
uv run python -m rust_twins_mut ./seeds \
    --processes 8 \
    --timeout 7200 \
    --api-timeout 180 \
    --grace-period 60 \
    --output ./my_output
```

### CLI Options

| Option | Default | Description |
|--------|---------|-------------|
| `folder` | (required) | Folder containing `.rs` files (searched recursively) |
| `--processes` | 4 | Number of parallel worker processes |
| `--timeout` | 3600 | Global timeout in seconds (soft — stops new tasks) |
| `--api-timeout` | 120 | Per-call API timeout in seconds |
| `--grace-period` | 30 | Seconds to wait for running tasks after timeout |
| `--output` | `./fuzz_output` | Output directory for mutated files |

## Archiving Results

After a run, bundle the output directory into a single `.tar.gz`:

```bash
./archive_results.sh ./fuzz_output                        # auto-named with timestamp
./archive_results.sh ./fuzz_output my_experiment.tar.gz   # custom name
```

## Mutation Types

| # | Name | Description |
|---|------|-------------|
| 1 | `duplicate_stmt` | Duplicate a non-declaration statement |
| 2 | `delete_stmt` | Delete a statement and dependent code |
| 3 | `change_control_flow` | Add/remove break, continue, or return in loops |
| 4 | `delete_expression` | Delete sub-expressions |
| 5 | `expand_expression` | Expand sub-expressions randomly |
| 6 | `replace_by_constant` | Replace expression with same-type constant |
| 7 | `flip_bit` | Flip a bit in a constant |
| 8 | `replace_digit` | Flip sign or change a digit |
| 9 | `change_type` | Change expression type (must compile) |
| 10 | `replace_unary_operator` | Replace unary op with assignment |
| 11 | `flip_operator` | Replace one operator with another |
| 12 | `replace_function_body` | Swap function body with another |
| 13 | `combine_functions` | Merge two function bodies |
| 14 | `lifetime` | Add lifetime annotations |
| 15 | `outlive` | Add outlive relationships between lifetimes |
| 16 | `ownership` | Make ownership more complex |
| 17 | `unsafe` | Introduce unsafe blocks and raw pointers |
| 18 | `replace_ap` | Replace arbitrary code segment |
| 19 | `use_var` | Insert expression using existing variables |
| 20 | `intro_var` | Insert new variable declarations |
