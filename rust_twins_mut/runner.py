"""Multiprocessing runner for continuous LLM-based Rust mutation."""

import sys
import time
import random
import signal
from collections import defaultdict
from datetime import datetime
from multiprocessing import Pool, Value, Lock
from pathlib import Path

# Import GPTOSSClient from the git submodule
sys.path.insert(0, str(Path(__file__).parent.parent / "gpt-oss-20b-google-cloud-call"))
from client import GPTOSSClient

from .mutator import extract_rust_code
from .prompts import prompt_dict

# Global state for worker processes
WORKER_ID = 0
counter_lock = None
stop_flag = None


def _init_worker(wid_counter, lock, stop):
    """Initialize worker process with shared counter, lock, and stop flag."""
    global WORKER_ID, counter_lock, stop_flag
    counter_lock = lock
    stop_flag = stop
    with lock:
        wid_counter.value += 1
        WORKER_ID = wid_counter.value


def _worker(config_tuple):
    """Worker function for multiprocessing.

    Performs a single mutation on a randomly selected Rust file.

    Args:
        config_tuple: (rust_codes, output_dir, log_file, api_timeout)

    Returns:
        (success, worker_id) tuple.
    """
    time.sleep(0.1)  # Small delay to prevent tight loop

    global WORKER_ID, counter_lock, stop_flag

    rust_codes, output_dir, log_file, api_timeout = config_tuple

    if stop_flag.value == 1:
        return (False, WORKER_ID)

    # Pick random file and mutation
    filepath, rust_code = random.choice(rust_codes)
    mutator_name = random.choice(list(prompt_dict.keys()))
    prompt_template = prompt_dict[mutator_name]
    prompt = f"<s>{prompt_template.format(input=rust_code).strip()}"

    print(f"[Worker {WORKER_ID}] Selected: {filepath} | Mutation: {mutator_name}")

    # Create client and call LLM
    try:
        client = GPTOSSClient()
        response = client.get_text(prompt)
    except Exception as e:
        print(f"[Worker {WORKER_ID}] LLM error: {e}")
        return (False, WORKER_ID)

    if not response:
        print(f"[Worker {WORKER_ID}] Failed to get LLM response")
        return (False, WORKER_ID)

    # Extract Rust code from response
    mutated_code = extract_rust_code(response)
    if not mutated_code:
        print(f"[Worker {WORKER_ID}] Failed to extract Rust code from response")
        return (False, WORKER_ID)

    # Write output file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    output_filename = f"mutated_{mutator_name}_{timestamp}_w{WORKER_ID}.rs"
    output_path = Path(output_dir) / output_filename

    try:
        with open(output_path, 'w') as f:
            f.write(mutated_code)
    except OSError as e:
        print(f"[Worker {WORKER_ID}] Error writing output file: {e}")
        return (False, WORKER_ID)

    # Log the result
    log_msg = (
        f"{datetime.now().isoformat()} | Worker {WORKER_ID} "
        f"| {output_filename} | Mutation: {mutator_name} | Source: {filepath}\n"
    )
    try:
        with open(log_file, 'a') as f:
            f.write(log_msg)
    except OSError as e:
        print(f"[Worker {WORKER_ID}] Error writing to log file: {e}")

    print(f"[Worker {WORKER_ID}] Success -> {output_filename}")
    return (True, WORKER_ID)


def continuous_fuzzing(folder_path, num_processes, global_timeout, output_dir, api_timeout, grace_period):
    """Run continuous LLM-based mutation using a multiprocessing pool.

    - Recursively collects .rs files from folder_path
    - Uses multiprocessing.Pool for parallel execution
    - Runs until global_timeout (soft: stops new tasks)
    - api_timeout applies to individual LLM calls (hard)
    - Graceful shutdown with configurable grace_period
    """
    folder = Path(folder_path).resolve()

    if not folder.exists():
        print(f"Error: Folder {folder} does not exist")
        return

    # Find all .rs files recursively
    rust_files = list(folder.rglob("*.rs"))
    if not rust_files:
        print(f"No .rs files found in {folder} (searched recursively)")
        return

    # Group files by directory for reporting
    files_by_dir = defaultdict(list)
    for rust_file in rust_files:
        rel_path = rust_file.relative_to(folder)
        parent_dir = str(rel_path.parent) if rel_path.parent != Path('.') else "."
        files_by_dir[parent_dir].append(rust_file)

    print(f"Found {len(rust_files)} Rust files in {folder} (searched recursively)")
    print(f"Files distributed across {len(files_by_dir)} directories:")
    for dir_name, files in sorted(files_by_dir.items()):
        print(f"  {dir_name}: {len(files)} files")
    print()

    # Create output directory and log file
    output_path = Path(output_dir).resolve()
    output_path.mkdir(parents=True, exist_ok=True)

    start_time = datetime.now()
    log_filename = f"fuzzing_log_{start_time.strftime('%Y%m%d_%H%M%S')}.txt"
    log_file = output_path / log_filename

    with open(log_file, 'w') as f:
        f.write(f"Fuzzing started at: {start_time.isoformat()}\n")
        f.write(f"Input folder: {folder}\n")
        f.write(f"Number of processes: {num_processes}\n")
        f.write(f"Global timeout: {global_timeout}s (soft constraint - stops new tasks)\n")
        f.write(f"API timeout per call: {api_timeout}s (hard constraint - individual call timeout)\n")
        f.write(f"Grace period: {grace_period}s (time to wait for running tasks after timeout)\n")
        f.write(f"Output directory: {output_path}\n")
        f.write(f"Total Rust files found (recursive): {len(rust_files)}\n")
        f.write(f"Files distributed across {len(files_by_dir)} directories\n")
        f.write("-" * 80 + "\n\n")

    # Read all Rust files
    rust_codes = []
    for rust_file in rust_files:
        try:
            with open(rust_file, 'r') as f:
                content = f.read()
                rel_path = rust_file.relative_to(folder)
                rust_codes.append((str(rel_path), content))
        except Exception as e:
            print(f"Error reading {rust_file}: {e}")

    if not rust_codes:
        print("No valid Rust code to process")
        return

    # Log found files
    rs_files_log = output_path / "rs_files_found.txt"
    with open(rs_files_log, "w", encoding="utf-8") as log:
        for filepath, _ in rust_codes:
            log.write(str(filepath) + "\n")

    print(f"Loaded {len(rust_codes)} Rust code snippets")
    print(f"Starting continuous fuzzing with {num_processes} processes...")
    print(f"Global timeout: {global_timeout}s (soft) | API timeout: {api_timeout}s (hard)")
    print(f"Grace period for shutdown: {grace_period}s")
    print(f"Output directory: {output_path}")
    print(f"Log file: {log_file}")
    print("-" * 80)

    # Shared state for worker processes
    wid_counter = Value('i', 0)
    lock = Lock()
    stop = Value('i', 0)

    timeout_reached = False

    def timeout_handler(signum, frame):
        nonlocal timeout_reached
        print("\n" + "=" * 80)
        print("Global timeout reached (soft constraint)")
        print("Stopping submission of new tasks...")
        print(f"Will wait up to {grace_period}s for running tasks to complete")
        print("=" * 80)
        timeout_reached = True
        stop.value = 1

    def signal_handler(signum, frame):
        nonlocal timeout_reached
        print("\n" + "=" * 80)
        print("Keyboard interrupt received")
        print("Stopping fuzzing...")
        print("=" * 80)
        timeout_reached = True
        stop.value = 1

    if hasattr(signal, 'SIGALRM'):
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(global_timeout)

    original_sigint = signal.signal(signal.SIGINT, signal_handler)

    successful_mutations = 0
    failed_mutations = 0

    try:
        with Pool(processes=num_processes, initializer=_init_worker, initargs=(wid_counter, lock, stop)) as pool:
            pending_results = []
            task_config = (rust_codes, output_path, log_file, api_timeout)

            while not timeout_reached:
                # Keep pool busy
                while len(pending_results) < num_processes * 2 and not timeout_reached:
                    result = pool.apply_async(_worker, (task_config,))
                    pending_results.append(result)

                # Collect completed tasks
                completed = []
                for i, result in enumerate(pending_results):
                    if result.ready():
                        try:
                            success, worker_id = result.get(timeout=0.1)
                            if success:
                                successful_mutations += 1
                            else:
                                failed_mutations += 1
                        except Exception as e:
                            print(f"Task error: {e}")
                            failed_mutations += 1
                        completed.append(i)

                for i in reversed(completed):
                    pending_results.pop(i)

                time.sleep(0.01)

            # Graceful shutdown
            print(f"\nGraceful shutdown initiated")
            print(f"Pending tasks: {len(pending_results)}")
            print(f"Waiting up to {grace_period}s for running tasks to complete...")

            shutdown_start = time.time()
            while pending_results and (time.time() - shutdown_start) < grace_period:
                completed = []
                for i, result in enumerate(pending_results):
                    if result.ready():
                        try:
                            success, worker_id = result.get(timeout=0.1)
                            if success:
                                successful_mutations += 1
                            else:
                                failed_mutations += 1
                        except Exception as e:
                            print(f"Task error during shutdown: {e}")
                            failed_mutations += 1
                        completed.append(i)

                for i in reversed(completed):
                    pending_results.pop(i)

                time.sleep(0.1)

            if pending_results:
                print(f"\nGrace period expired. {len(pending_results)} tasks did not complete.")

            pool.close()
            pool.join()

    except KeyboardInterrupt:
        print("\n" + "=" * 80)
        print("Keyboard interrupt - forcing shutdown")
        print("=" * 80)
    finally:
        if hasattr(signal, 'SIGALRM'):
            signal.alarm(0)
        signal.signal(signal.SIGINT, original_sigint)

    # Summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    total = successful_mutations + failed_mutations
    summary = f"""
{"-" * 80}
Fuzzing completed at: {end_time.isoformat()}
Total duration: {duration:.2f} seconds
Successful mutations: {successful_mutations}
Failed/cancelled: {failed_mutations}
Total tasks: {total}
"""

    print("\n" + "=" * 80)
    print(summary)
    print("=" * 80)

    with open(log_file, 'a') as f:
        f.write(summary)
