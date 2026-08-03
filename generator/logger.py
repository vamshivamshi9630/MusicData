import sys

def log_step(step_num: int, total_steps: int, title: str):
    print(f"\n[{step_num}/{total_steps}] [STEP] {title}...")

def log_info(msg: str):
    print(f"  |-- {msg}")

def log_success(msg: str):
    print(f"[SUCCESS] {msg}")

def log_error(msg: str):
    print(f"[ERROR] {msg}", file=sys.stderr)
