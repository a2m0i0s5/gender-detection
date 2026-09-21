import subprocess
import sys
import os

if __name__ == '__main__':
    # Get current script folder and target detect.py path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    detect_script = os.path.join(script_dir, "detect.py")
    
    # Run detect.py with the same command line arguments passed to this script
    cmd = [sys.executable, detect_script] + sys.argv[1:]
    
    # Execute the script and wait for it to complete
    result = subprocess.run(cmd)
    sys.exit(result.returncode)