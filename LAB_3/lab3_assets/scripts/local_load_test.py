"""LAB3 safe local-only load demonstration.
Hard-coded to 127.0.0.1:8080. It refuses any remote target.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.request import urlopen
from time import perf_counter

URL = "http://127.0.0.1:8080/"
TOTAL_REQUESTS = 50
MAX_WORKERS = 5
TIMEOUT_SECONDS = 3


def one_request(i: int):
    start = perf_counter()
    with urlopen(URL, timeout=TIMEOUT_SECONDS) as r:
        body = r.read(256)
        status = r.status
    return i, status, len(body), perf_counter() - start


def main():
    if not URL.startswith("http://127.0.0.1:8080/"):
        raise SystemExit("Safety check failed: target must remain 127.0.0.1:8080")
    started = perf_counter()
    ok = 0
    failures = 0
    latencies = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = [pool.submit(one_request, i) for i in range(TOTAL_REQUESTS)]
        for f in as_completed(futures):
            try:
                _, status, _, latency = f.result()
                if status == 200:
                    ok += 1
                else:
                    failures += 1
                latencies.append(latency)
            except Exception:
                failures += 1
    elapsed = perf_counter() - started
    avg = sum(latencies) / len(latencies) if latencies else 0.0
    print(f"target={URL}")
    print(f"requests={TOTAL_REQUESTS} workers={MAX_WORKERS}")
    print(f"ok={ok} failures={failures}")
    print(f"elapsed_s={elapsed:.3f} avg_latency_s={avg:.4f}")


if __name__ == "__main__":
    main()
