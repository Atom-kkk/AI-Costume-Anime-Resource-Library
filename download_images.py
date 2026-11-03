import json, os, sys, time
from concurrent.futures import ThreadPoolExecutor
import urllib.request

BASE = "https://ai-costume-anime-gallery.pages.dev/"
ROOT = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(os.path.dirname(ROOT), "site", "data.json"), encoding="utf-8"))

jobs = []
for d in data:
    jobs.append(("thumbs", d["サムネ"].split("/")[-1]))
    jobs.append(("img", d["画像"].split("/")[-1]))

for sub in ("thumbs", "img"):
    os.makedirs(os.path.join(ROOT, sub), exist_ok=True)


def fetch(job):
    sub, name = job
    out = os.path.join(ROOT, sub, name)
    if os.path.exists(out) and os.path.getsize(out) > 512:
        return "skip"
    url = BASE + sub + "/" + name
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                buf = r.read()
            if len(buf) < 512:
                raise ValueError("too small: %d" % len(buf))
            tmp = out + ".part"
            with open(tmp, "wb") as f:
                f.write(buf)
            os.replace(tmp, out)
            return "ok"
        except Exception as e:
            if attempt == 4:
                return "FAIL %s %s: %s" % (sub, name, e)
            time.sleep(1.2 * (attempt + 1))


done = 0
fails = []
with ThreadPoolExecutor(max_workers=12) as ex:
    for res in ex.map(fetch, jobs):
        done += 1
        if res.startswith("FAIL"):
            fails.append(res)
        if done % 200 == 0:
            print("进度 %d/%d  失败 %d" % (done, len(jobs), len(fails)), flush=True)

print("完成 %d，失败 %d" % (done, len(fails)))
for f in fails[:30]:
    print(f)
