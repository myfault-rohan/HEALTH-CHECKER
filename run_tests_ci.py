import subprocess
import sys
import urllib.request
import urllib.parse
import json

def main():
    print("=== Running pytest via Python CI Runner ===")
    cmd = [
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
        
        # Upload to file.io
        try:
            print("Uploading log to file.io...")
            boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
            data = []
            data.append(f"--{boundary}".encode('utf-8'))
            data.append(f'Content-Disposition: form-data; name="file"; filename="{log_file}"'.encode('utf-8'))
            data.append(b'Content-Type: text/plain')
            data.append(b'')
            data.append(result.stdout.encode('utf-8'))
            data.append(f"--{boundary}--".encode('utf-8'))
            data.append(b'')
            body = b'\r\n'.join(data)
            
            req = urllib.request.Request(
                "https://file.io",
                data=body,
                headers={
                    "Content-Type": f"multipart/form-data; boundary={boundary}",
                    "User-Agent": "Mozilla/5.0"
                }
            )
            with urllib.request.urlopen(req) as resp:
                resp_data = json.loads(resp.read().decode())
                link = resp_data.get("link", "Upload failed - no link in response")
                print(f"Uploaded log link: {link}")
                print(f"::error::Pytest failed (code {result.returncode}). Download log: {link}")
        except Exception as e:
            print(f"Failed to upload log to file.io: {e}")
            # If upload fails, let's print the last 150 lines of stdout so it's guaranteed visible in runner stdout/stderr
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
