import subprocess
import sys

def main():
    print("=== Running pytest via Python CI Runner ===")
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/",
        "--cov=app",
        "--cov=predictor",
        "--cov-report=term-missing",
        "--cov-report=xml",
        "-m", "not slow",
        "-v"
    ]
    
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    print(result.stdout)
    
    if result.returncode != 0:
        print(f"=== Pytest failed with exit code {result.returncode} ===")
        # Write log to file
        log_file = "pytest_output.log"
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(result.stdout)
        
        # Try pushing to debug branch
        try:
            print("Committing and pushing logs to ci-debug branch...")
            subprocess.run(["git", "config", "--global", "user.name", "GitHub Actions"])
            subprocess.run(["git", "config", "--global", "user.email", "actions@github.com"])
            subprocess.run(["git", "checkout", "-b", "ci-debug"])
            subprocess.run(["git", "add", "-f", "pytest_output.log"])
            subprocess.run(["git", "commit", "-m", "chore: pytest failure logs [skip ci]"])
            subprocess.run(["git", "push", "origin", "ci-debug", "-f"])
            print("Successfully pushed logs to ci-debug branch!")
        except Exception as ge:
            print(f"Failed to push git logs: {ge}")

        # Print last 150 lines of pytest output to stdout so it's guaranteed visible in the console
        print("=== Last 150 lines of pytest output ===")
        lines = result.stdout.splitlines()
        for line in lines[-150:]:
            print(line)
                
        sys.exit(result.returncode)
    else:
        print("=== Pytest passed! ===")
        sys.exit(0)

if __name__ == "__main__":
    main()
