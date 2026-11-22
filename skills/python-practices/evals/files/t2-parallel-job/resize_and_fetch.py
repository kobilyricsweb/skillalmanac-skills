"""Download 40 image URLs and compute a perceptual hash for each (pure Python loop, about 300 ms per image)."""
import threading
import urllib.request


def fetch(url):
    return urllib.request.urlopen(url).read()


def phash(data):
    value = 0
    for i, byte in enumerate(data):
        value = (value * 31 + byte * (i % 7 + 1)) % (2 ** 61 - 1)
    return value


def worker(url, results):
    results[url] = phash(fetch(url))


def run(urls):
    results = {}
    threads = [threading.Thread(target=worker, args=(u, results)) for u in urls]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return results


run(["https://example.com/a.png"] * 40)
