"""
CrowdPulse AI - Demo Ticket Generator
Generates 50 sample QR-code tickets and saves them as:
  - demo/tickets.json        (structured data)
  - demo/qr_codes/T0001.png  (QR code images, if qrcode lib is available)
"""

import json
import os
import random
import sys
from pathlib import Path

# ── Ticket configuration ──────────────────────────────────────

FIRST_NAMES = [
    "Rahul", "Priya", "Amit", "Sneha", "Vikas", "Ananya", "Rohan", "Kavita",
    "Sanjay", "Meera", "Arjun", "Divya", "Raj", "Neha", "Karan", "Pooja",
    "Suresh", "Lakshmi", "Varun", "Nisha", "Aditya", "Ritu", "Mohit", "Swati",
    "Deepak", "Anjali",
]

LAST_NAMES = [
    "Sharma", "Patel", "Singh", "Kumar", "Gupta", "Reddy", "Das", "Mehta",
    "Joshi", "Iyer", "Chopra", "Verma", "Nair", "Pillai", "Rao", "Bhatia",
]

GATES = ["Gate 1", "Gate 2", "Gate 3", "Gate 4", "Gate 5"]
STANDS = ["North Stand", "East Stand", "West Stand", "South Stand"]
SEAT_LETTERS = "ABCDEFGHIJKLMNOP"

NUM_TICKETS = 50


def _generate_ticket(index: int) -> dict:
    """Generate one ticket dict."""
    ticket_id = f"T{index:04d}"
    gate = random.choice(GATES)
    stand = random.choice(STANDS)
    seat_letter = random.choice(SEAT_LETTERS)
    seat_num = random.randint(1, 60)
    seat = f"{seat_letter}-{seat_num}"
    name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

    return {
        "id": ticket_id,
        "gate": gate,
        "stand": stand,
        "seat": seat,
        "name": name,
    }


def main():
    demo_dir = Path(__file__).parent
    demo_dir.mkdir(parents=True, exist_ok=True)

    # ── Generate ticket data ──────────────────────────────────
    tickets = [_generate_ticket(i + 1) for i in range(NUM_TICKETS)]

    tickets_json_path = demo_dir / "tickets.json"
    with open(tickets_json_path, "w", encoding="utf-8") as f:
        json.dump(tickets, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved {NUM_TICKETS} tickets to {tickets_json_path}")

    # ── Generate QR code images ───────────────────────────────
    qr_dir = demo_dir / "qr_codes"
    qr_dir.mkdir(exist_ok=True)

    try:
        import qrcode  # type: ignore
        _generate_with_qrcode_lib(tickets, qr_dir)
    except ImportError:
        print("ℹ️  'qrcode' package not installed — trying OpenCV QRCodeEncoder …")
        try:
            _generate_with_opencv(tickets, qr_dir)
        except Exception as exc:
            print(f"⚠️  QR image generation unavailable ({exc}).")
            print("   tickets.json was still saved. You can install 'qrcode' and rerun.")
            _print_terminal_qr_samples(tickets[:3])


def _generate_with_qrcode_lib(tickets: list[dict], qr_dir: Path):
    """Generate QR PNGs using the `qrcode` library."""
    import qrcode  # type: ignore

    for t in tickets:
        data = json.dumps(t)
        img = qrcode.make(data)
        path = qr_dir / f"{t['id']}.png"
        img.save(str(path))

    print(f"✅ Generated {len(tickets)} QR images in {qr_dir}")


def _generate_with_opencv(tickets: list[dict], qr_dir: Path):
    """Generate QR PNGs using OpenCV's QRCodeEncoder (4.x+)."""
    import cv2
    import numpy as np

    encoder = cv2.QRCodeEncoder.create()
    for t in tickets:
        data = json.dumps(t)
        qr_img = encoder.encode(data)
        if qr_img is not None:
            # Resize for readability
            qr_img = cv2.resize(qr_img, (400, 400), interpolation=cv2.INTER_NEAREST)
            path = qr_dir / f"{t['id']}.png"
            cv2.imwrite(str(path), qr_img)

    print(f"✅ Generated {len(tickets)} QR images in {qr_dir} (OpenCV)")


def _print_terminal_qr_samples(tickets: list[dict]):
    """Print a couple of tickets as JSON for manual QR generation."""
    print("\n── Sample ticket JSON (copy into any QR generator) ──")
    for t in tickets:
        print(json.dumps(t))
    print()


if __name__ == "__main__":
    main()
