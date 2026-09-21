"""Mo phong 1 su kien: dang ky -> check-in -> dem email trong Mailpit

Cac lenh: register, checkin, report (xem --help).
"""

import argparse
import json
import random
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

RETRY_STATUS = {429, 502, 503, 504}
RETRY_SLEEP = 3
REQUEST_TIMEOUT = 5


def call(method, url, payload=None):
    """Tra ve (status, json). Loi HTTP van tra ve status, khong raise."""
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(
        url, data=data, method=method, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            status, raw = resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        status, raw = exc.code, exc.read()
    try:
        return status, json.loads(raw)
    except ValueError:
        return status, None


def call_retry(method, url, payload, label, max_wait):
    """Thu lai khi mat ket noi, timeout, 429/502/503/504 (service dang duoc restart)."""
    deadline = time.monotonic() + max_wait
    attempt = 0
    while True:
        attempt += 1
        try:
            status, body = call(method, url, payload)
            if status not in RETRY_STATUS:
                return status, body
            reason = f"HTTP {status}"
        except OSError as exc:
            reason = type(exc).__name__
        if time.monotonic() >= deadline:
            sys.exit(f"{label}: het thoi gian cho ({reason})")
        print(f"  {label}: {reason}, thu lai sau {RETRY_SLEEP}s (lan {attempt})")
        time.sleep(RETRY_SLEEP)


def save_state(path, state):
    Path(path).write_text(json.dumps(state, indent=2))


def load_state(path):
    if not Path(path).exists():
        sys.exit(f"Khong thay {path}. Chay lenh 'register' truoc.")
    return json.loads(Path(path).read_text())


def maybe_pause(i, pause_after):
    if pause_after and i == pause_after:
        print("\n>>> TAM DUNG: chay lenh gay loi o phien khac.")
        input(">>> Xong thi nhan Enter de tiep tuc... ")


def cmd_register(args):
    base = args.base_url.rstrip("/")
    when = datetime.now(timezone.utc)
    status, event = call_retry(
        "POST",
        f"{base}/events",
        {
            "name": f"Demo {when:%Y-%m-%d %H:%M}",
            "description": "Su kien gia lap",
            "location": "HCMC",
            "start_time": (when + timedelta(days=7))
            .replace(microsecond=0, tzinfo=None)
            .isoformat(),
            "capacity": args.count,
        },
        "tao event",
        args.max_wait,
    )
    if status != 201:
        sys.exit(f"Tao event that bai: {status} {event}")
    event_id = event["id"]
    print(f"Event {event_id}, suc chua {args.count}")

    url = f"{base}/events/{event_id}/register"
    tickets = []
    for i in range(1, args.count + 1):
        status, body = call_retry(
            "POST",
            url,
            {"full_name": f"Demo User {i:03d}", "email": f"demo{i:03d}@example.com"},
            f"dang ky #{i}",
            args.max_wait,
        )
        if status != 201:
            sys.exit(f"Dang ky #{i} that bai: {status} {body}")
        tickets.append({"ticket_id": body["ticket_id"], "email": body["email"]})
        print(f"[{i}/{args.count}] ve {body['ticket_id']}")
        maybe_pause(i, args.pause_after)
        time.sleep(args.delay)

    save_state(args.state, {"event_id": event_id, "tickets": tickets})

    status, body = call_retry(
        "POST",
        url,
        {"full_name": "Demo Extra", "email": "extra@example.com"},
        "dang ky them",
        args.max_wait,
    )
    print(f"\nDang ky them 1 nguoi khi da het cho -> {status} {body}")
    if status != 400:
        print("SAI: mong doi 400 (het cho)")
        return 1
    print(f"Da luu {len(tickets)} ve vao {args.state}")


def fetch_qr_dir(args):
    if args.qr_dir:
        return Path(args.qr_dir)
    dest = Path("demo-qr")
    shutil.rmtree(dest, ignore_errors=True)
    subprocess.run(
        ["docker", "cp", f"{args.container}:/app/qrcodes", str(dest)], check=True
    )
    return dest


def tamper(token):
    """Doi 1 ky tu o giua chu ky -> chu ky sai."""
    head, payload, sig = token.split(".")
    mid = len(sig) // 2
    bad = "B" if sig[mid] == "A" else "A"
    return ".".join([head, payload, sig[:mid] + bad + sig[mid + 1 :]])


def cmd_checkin(args):
    try:
        from PIL import Image
        from pyzbar.pyzbar import decode
    except ImportError:
        sys.exit("Thieu pyzbar/pillow: dung python cua ~/tmp-qr-venv (xem guide).")

    state = load_state(args.state)
    ids = [t["ticket_id"] for t in state["tickets"]]
    qr_dir = fetch_qr_dir(args)
    tokens = {}
    for tid in ids:
        found = decode(Image.open(qr_dir / f"{tid}.png"))
        if not found:
            sys.exit(f"Khong doc duoc QR cua ve {tid}")
        tokens[tid] = found[0].data.decode()
    print(f"Da doc {len(tokens)} ma QR")

    url = f"{(args.checkin_url or args.base_url).rstrip('/')}/checkin"
    chosen = random.Random(args.seed).sample(ids, round(len(ids) * args.rate))
    print(f"Check-in ngau nhien {len(chosen)}/{len(ids)} ve\n")

    scanned, already, failed = [], 0, 0
    for i, tid in enumerate(chosen, 1):
        status, _ = call_retry(
            "POST", url, {"token": tokens[tid]}, f"check-in #{i}", args.max_wait
        )
        print(f"[{i}/{len(chosen)}] {tid} -> {status}")
        if status == 201:
            scanned.append(tid)
        elif status == 409:
            already += 1
            scanned.append(tid)
        else:
            failed += 1
        maybe_pause(i, args.pause_after)
        time.sleep(args.delay)

    print("\nQuet lai ve da check-in (mong doi 409):")
    dup_targets = scanned[: args.dups]
    dup_ok = 0
    for tid in dup_targets:
        status, _ = call_retry(
            "POST", url, {"token": tokens[tid]}, "quet lai", args.max_wait
        )
        print(f"  {tid} -> {status}")
        dup_ok += status == 409

    print("\nQuet 1 ve gia (chu ky bi sua, mong doi 401):")
    victim = next((t for t in ids if t not in chosen), ids[0])
    status, _ = call_retry(
        "POST", url, {"token": tamper(tokens[victim])}, "ve gia", args.max_wait
    )
    print(f"  {victim} -> {status}")
    forged_ok = status == 401

    print("\n=== Ket qua ===")
    print(f"Ve da dang ky:            {len(ids)}")
    print(f"Check-in thanh cong:      {len(scanned) - already} (201)")
    print(f"Da ghi nhan tu truoc:     {already} (409 o luot dau)")
    print(f"Check-in that bai:        {failed}")
    print(f"Quet lai bi chan:         {dup_ok}/{len(dup_targets)} (409)")
    print(f"Ve gia bi tu choi:        {int(forged_ok)}/1 (401)")
    print(f"Chua check-in:            {len(ids) - len(scanned)}")
    if failed or dup_ok != len(dup_targets) or not forged_ok:
        return 1


def cmd_report(args):
    state = load_state(args.state)
    ids = [t["ticket_id"] for t in state["tickets"]]
    mailpit = args.mailpit_url.rstrip("/")
    deadline = time.monotonic() + args.wait
    found = set()
    while True:
        for tid in ids:
            if tid in found:
                continue
            try:
                status, body = call(
                    "GET", f"{mailpit}/api/v1/search?query={urllib.parse.quote(tid)}"
                )
            except OSError as exc:
                sys.exit(f"Khong goi duoc Mailpit ({exc}). Kiem tra --mailpit-url.")
            if status == 200 and body and body.get("messages"):
                found.add(tid)
        print(f"Email trong Mailpit: {len(found)}/{len(ids)}")
        if len(found) == len(ids) or time.monotonic() >= deadline:
            break
        time.sleep(10)
    if len(found) != len(ids):
        return 1


def build_parser():
    parser = argparse.ArgumentParser(description="Mo phong su kien check-in")
    parser.add_argument("--state", default="demo_state.json")
    sub = parser.add_subparsers(dest="command", required=True)

    reg = sub.add_parser("register", help="tao event va dang ky N nguoi")
    reg.add_argument("--base-url", required=True)
    reg.add_argument("--count", type=int, default=20)
    reg.add_argument("--delay", type=float, default=0.3)
    reg.add_argument("--pause-after", type=int, default=0)
    reg.add_argument("--max-wait", type=int, default=420)
    reg.set_defaults(func=cmd_register)

    chk = sub.add_parser("checkin", help="check-in ngau nhien, quet lai, ve gia")
    chk.add_argument("--base-url", required=True)
    chk.add_argument("--checkin-url", default="")
    chk.add_argument(
        "--container", default="event_checkin_system-registration-service-1"
    )
    chk.add_argument("--qr-dir", default="")
    chk.add_argument("--rate", type=float, default=0.7)
    chk.add_argument("--dups", type=int, default=3)
    chk.add_argument("--seed", type=int, default=42)
    chk.add_argument("--delay", type=float, default=0.5)
    chk.add_argument("--pause-after", type=int, default=0)
    chk.add_argument("--max-wait", type=int, default=420)
    chk.set_defaults(func=cmd_checkin)

    rep = sub.add_parser("report", help="dem email trong Mailpit")
    rep.add_argument("--mailpit-url", default="http://127.0.0.1:8025")
    rep.add_argument("--wait", type=int, default=0)
    rep.set_defaults(func=cmd_report)
    return parser


if __name__ == "__main__":
    args = build_parser().parse_args()
    sys.exit(args.func(args) or 0)
