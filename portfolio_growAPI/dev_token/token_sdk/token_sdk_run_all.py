import subprocess, sys
from pathlib import Path


def run_parallel_sdk():
    print("Starting Parallel SDK token Audit")
    script = Path(__file__).parent / "dev_token_sdk_cc.py"

    procs = [subprocess.Popen([sys.executable, str(script), biz])
             for biz in ["patur", "murshe", "amuta", "shutfut"]]

    exit_codes = [p.wait() for p in procs]

    if any(code != 0 for code in exit_codes):
        print("One or more SDK processes failed.")
        sys.exit(1)

    print("All SDK token automations finished successfully.")


if __name__ == "__main__":
    run_parallel_sdk()