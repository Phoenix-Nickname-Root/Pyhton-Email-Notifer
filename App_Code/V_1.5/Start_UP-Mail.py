#
# Uptime Monitor with Crash Detection
# Copyright (C) 2026 Phoenix_Nickname_Root
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#

import os
import sys
import json
import time
import datetime
import yagmail
import signal

# ------------------------
# detect where the compiled script is running
# ------------------------
BASE_PATH = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))

CONFIG_PATH = os.path.join(BASE_PATH, "config.json")
DATA_FILE = os.path.join(BASE_PATH, "server_runtime.txt")

# ------------------------
# Load config
# ------------------------
if not os.path.exists(CONFIG_PATH):
    print(f"Config not found: {CONFIG_PATH}")
    sys.exit(1)

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)

# ------------------------
# Mail init
# ------------------------
yag = yagmail.SMTP(
    {config["user"]: config["name"]},
    config["password"],
    config["smtp_host"],
    config["smtp_port"]
)

TO_EMAIL = config["mail_reciver"]

SUBJECT_UP = "!WakeUp"
SUBJECT_DOWN = "!Shutdown"
SUBJECT_CRASH = "!CrashDetected"

# ------------------------
# Helpers
# ------------------------
def send_email(subject, body):
    yag.send(to=TO_EMAIL, subject=subject, contents=body)

def format_seconds(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    return f"{d}d {h:02}h {m:02}m {s:02}s"

def read_runtime():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = f.read().strip()
            if data:
                return map(float, data.split(","))
    return None, None

def write_runtime(start, current):
    with open(DATA_FILE, "w") as f:
        f.write(f"{start},{current}")

def format_dt(ts):
    dt = datetime.datetime.fromtimestamp(ts)
    return dt.strftime("%d-%m-%Y"), dt.strftime("%H:%M:%S")

def build_body(title, text, sd, st, ed=None, et=None):
    body = (
        f"#################################\n"
        f"######### {title} #########\n"
        f"#################################\n"
        f"{text}\n"
        f"---------------------------------\n"
        f"Start Date: {sd}\n"
        f"Start Time: {st}\n"
    )

    if ed and et:
        body += f"=============\nEnd Date: {ed}\nEnd Time: {et}\n"

    body += (
        f"---------------------------------\n"
        f"This is an automatic notification\n"
        f"---------------------------------\n"
        f"(C) 2026 code by Phoenix_Nickname_Root\n"
        f"https://github.com/Phoenix-Nickname-Root\n"
        f"#################################"
    )
    return body

# ------------------------
# Shutdown handler
# ------------------------
def on_exit(signum, frame):
    now = time.time()
    start, _ = read_runtime()

    if start:
        sd, st = format_dt(start)
        ed, et = format_dt(now)

        uptime = format_seconds(int(now - start))

        body = build_body(
            "Shutdown",
            f"Server is shutting down\nUptime: {uptime}",
            sd, st, ed, et
        )

        send_email(SUBJECT_DOWN, body)

    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)

    sys.exit(0)

signal.signal(signal.SIGINT, on_exit)
signal.signal(signal.SIGTERM, on_exit)

# ------------------------
# Main
# ------------------------
def main():
    now = time.time()
    start, last = read_runtime()

    # ---- Crash detect ----
    if start and last:
        sd, st = format_dt(start)
        cd, ct = format_dt(last)

        uptime = format_seconds(int(last - start))

        body = build_body(
            "Crash Detected",
            f"Previous server crashed\nLast uptime: {uptime}",
            sd, st, cd, ct
        )

        send_email(SUBJECT_CRASH, body)

    # ---- Start ----
    start = now
    write_runtime(start, now)

    sd, st = format_dt(start)

    body = build_body(
        "Server Started",
        "Server started successfully",
        sd, st
    )

    send_email(SUBJECT_UP, body)

    # ---- Loop ----
    while True:
        write_runtime(start, time.time())
        time.sleep(1)

# ------------------------
if __name__ == "__main__":
    main()