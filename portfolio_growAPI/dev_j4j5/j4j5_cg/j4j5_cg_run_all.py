import subprocess, sys
from pathlib import Path

def run():
    print("Starting Parallel CG Two-Step Flow (J4/J5)")
    script = Path(__file__).parent / "dev_j4j5_cg.py"


    procs = [subprocess.Popen([sys.executable, str(script), biz])
             for biz in ["patur", "murshe", "amuta", "shutfut"]]


    [p.wait() for p in procs]
    print("\n All CG J4/J5 processes completed.")

if __name__ == "__main__":
    run()