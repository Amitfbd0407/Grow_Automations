import subprocess, sys
from pathlib import Path


def run():
    print("Starting Parallel DEV CG Two-Step Flow")
    script = Path(__file__).parent / "dev_token_cg.py"


    procs = [subprocess.Popen([sys.executable, str(script), biz])
             for biz in ["patur", "murshe", "amuta", "shutfut"]]


    [p.wait() for p in procs]
    print("\nAll processes completed.")


if __name__ == "__main__":
    run()