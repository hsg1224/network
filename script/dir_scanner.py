import requests
import sys

def scan_dirs(url, dict_file):
    with open(dict_file, 'r') as f:
        for line in f:
            path = line.strip()
            target = url.rstrip('/') + '/' + path
            try:
                resp = requests.get(target, timeout=3)
                if resp.status_code == 200:
                    print(f"[+] Found: {target}")
            except:
                pass

if __name__ == "__main__":
    scan_dirs(sys.argv[1], sys.argv[2])