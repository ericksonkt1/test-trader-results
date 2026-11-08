"""
Keeps the container alive and runs the Strategist every night.

Env:
  RUN_AT        "21:00" (local time in TZ)
  TZ            "America/Los_Angeles"
  RUN_ON_START  "1" to run once immediately when the container starts
  RUN_DAYS      "0,1,2,3,6" weekdays to run (Mon=0). Default: Sun-Thu nights,
                so fresh results are ready for each weekday morning brief.
"""
import logging
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

logging.basicConfig(level=logging.INFO, format="%(asctime)s scheduler %(message)s")
log = logging.getLogger()

TZ = ZoneInfo(os.environ.get("TZ", "America/Los_Angeles"))
HH, MM = map(int, os.environ.get("RUN_AT", "21:00").split(":"))
DAYS = {int(d) for d in os.environ.get("RUN_DAYS", "0,1,2,3,6").split(",")}
CMD = [sys.executable, "-m", "strategist.run", "--config", os.environ.get("CONFIG", "/app/config.json")]


def next_run(now):
    t = now.replace(hour=HH, minute=MM, second=0, microsecond=0)
    if t <= now:
        t += timedelta(days=1)
    while t.weekday() not in DAYS:
        t += timedelta(days=1)
    return t


def run():
    log.info("Starting Strategist run")
    rc = subprocess.call(CMD)
    log.info("Strategist finished with exit code %s", rc)
    if rc == 0:
        from strategist.publish import publish  # optional GitHub hand-off to the cloud desk
        publish(os.environ.get("DATA_DIR", "/data"))


if __name__ == "__main__":
    if os.environ.get("RUN_ON_START") == "1":
        run()
    while True:
        nxt = next_run(datetime.now(TZ))
        log.info("Next run: %s", nxt.isoformat())
        while datetime.now(TZ) < nxt:
            time.sleep(min(300, max(1, (nxt - datetime.now(TZ)).total_seconds())))
        run()
