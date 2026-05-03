import subprocess, sys
from pathlib import Path


def run_parallel_cc():
    print("🚀 Starting Parallel customer info regular Audit")
    script = Path(__file__).parent / "dev_regular_cc.py"

    procs = [subprocess.Popen([sys.executable, str(script), biz])
             for biz in ["patur", "murshe", "amuta", "shutfut"]]

    exit_codes = [p.wait() for p in procs]

    if any(code != 0 for code in exit_codes):
        print("One or more CC processes failed.")
        sys.exit(1)

    print("All CI regular automations finished successfully.")


if __name__ == "__main__":
    run_parallel_cc()