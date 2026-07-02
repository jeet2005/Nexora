"""Generate synthetic network traffic CSV for CyberShield demo.

Usage:
    python generate_sample_data.py [--rows 1000] [--anomaly-rate 0.05] [--output network_traffic.csv]
"""

from __future__ import annotations

import argparse
import csv
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROTOCOLS = ["TCP", "UDP", "ICMP", "DNS", "HTTP", "HTTPS", "SSH", "FTP"]
NORMAL_PROTOCOLS = ["TCP", "UDP", "HTTP", "HTTPS", "DNS"]
ANOMALY_PROTOCOLS = ["ICMP", "FTP", "SSH"]

TCP_FLAGS = ["SYN", "SYN-ACK", "ACK", "FIN", "RST", "PSH-ACK", "URG"]
NORMAL_FLAGS = ["SYN", "SYN-ACK", "ACK", "FIN", "PSH-ACK"]
ANOMALY_FLAGS = ["RST", "URG", "SYN"]  # port scan / flood signatures

INTERNAL_SUBNETS = ["10.0.1.", "10.0.2.", "10.0.3.", "192.168.1.", "192.168.10."]
EXTERNAL_IPS = [
    "203.0.113.",
    "198.51.100.",
    "185.220.101.",
    "45.33.32.",
    "91.189.89.",
    "8.8.8.",
    "1.1.1.",
    "104.16.249.",
    "151.101.1.",
    "172.217.14.",
]

FIELDNAMES = [
    "timestamp",
    "src_ip",
    "dst_ip",
    "src_port",
    "dst_port",
    "protocol",
    "bytes_sent",
    "bytes_received",
    "duration_ms",
    "packet_count",
    "tcp_flags",
    "is_encrypted",
]


def _rand_internal_ip() -> str:
    return random.choice(INTERNAL_SUBNETS) + str(random.randint(2, 254))


def _rand_external_ip() -> str:
    return random.choice(EXTERNAL_IPS) + str(random.randint(1, 254))


def _normal_row(ts: datetime) -> dict:
    src = _rand_internal_ip()
    dst = random.choice([_rand_external_ip(), _rand_internal_ip()])
    proto = random.choice(NORMAL_PROTOCOLS)
    return {
        "timestamp": ts.isoformat(),
        "src_ip": src,
        "dst_ip": dst,
        "src_port": random.randint(1024, 65535),
        "dst_port": random.choice([80, 443, 53, 22, 8080, 3306, 5432, 8443]),
        "protocol": proto,
        "bytes_sent": random.randint(40, 15_000),
        "bytes_received": random.randint(40, 50_000),
        "duration_ms": random.randint(1, 3000),
        "packet_count": random.randint(1, 50),
        "tcp_flags": random.choice(NORMAL_FLAGS),
        "is_encrypted": 1 if proto in ("HTTPS", "SSH") else random.choice([0, 0, 0, 1]),
    }


def _anomaly_row(ts: datetime) -> dict:
    """Generate an anomalous row — port scan, data exfil, or unusual protocol."""
    attack_type = random.choice(["port_scan", "data_exfil", "unusual_proto", "flood"])
    src = _rand_internal_ip() if random.random() < 0.4 else _rand_external_ip()
    dst = _rand_internal_ip() if random.random() < 0.6 else _rand_external_ip()

    if attack_type == "port_scan":
        return {
            "timestamp": ts.isoformat(),
            "src_ip": src,
            "dst_ip": dst,
            "src_port": random.randint(1024, 65535),
            "dst_port": random.randint(1, 1024),  # scanning low ports
            "protocol": "TCP",
            "bytes_sent": random.randint(40, 120),  # tiny packets
            "bytes_received": random.randint(0, 60),
            "duration_ms": random.randint(0, 5),  # very fast
            "packet_count": random.randint(1, 3),
            "tcp_flags": random.choice(["SYN", "RST"]),
            "is_encrypted": 0,
        }
    elif attack_type == "data_exfil":
        return {
            "timestamp": ts.isoformat(),
            "src_ip": _rand_internal_ip(),
            "dst_ip": _rand_external_ip(),
            "src_port": random.randint(1024, 65535),
            "dst_port": random.choice([443, 8443, 53]),  # disguised as legit
            "protocol": random.choice(["HTTPS", "DNS"]),
            "bytes_sent": random.randint(500_000, 5_000_000),  # huge upload
            "bytes_received": random.randint(100, 5000),
            "duration_ms": random.randint(100, 2000),
            "packet_count": random.randint(200, 2000),
            "tcp_flags": "PSH-ACK",
            "is_encrypted": 1,
        }
    elif attack_type == "flood":
        return {
            "timestamp": ts.isoformat(),
            "src_ip": src,
            "dst_ip": dst,
            "src_port": random.randint(1024, 65535),
            "dst_port": random.choice([80, 443]),
            "protocol": "TCP",
            "bytes_sent": random.randint(40, 200),
            "bytes_received": 0,
            "duration_ms": 0,
            "packet_count": random.randint(500, 5000),  # massive packet count
            "tcp_flags": random.choice(["SYN", "URG"]),
            "is_encrypted": 0,
        }
    else:  # unusual_proto
        return {
            "timestamp": ts.isoformat(),
            "src_ip": src,
            "dst_ip": dst,
            "src_port": random.randint(1024, 65535),
            "dst_port": random.choice([21, 23, 3389, 5900]),  # FTP/Telnet/RDP/VNC
            "protocol": random.choice(ANOMALY_PROTOCOLS),
            "bytes_sent": random.randint(1000, 100_000),
            "bytes_received": random.randint(1000, 100_000),
            "duration_ms": random.randint(5000, 60_000),  # long sessions
            "packet_count": random.randint(50, 500),
            "tcp_flags": random.choice(ANOMALY_FLAGS),
            "is_encrypted": 0,
        }


def generate(
    num_rows: int = 1000, anomaly_rate: float = 0.05, seed: int = 42
) -> list[dict]:
    random.seed(seed)
    rows: list[dict] = []
    base_time = datetime.now(timezone.utc) - timedelta(hours=1)

    for i in range(num_rows):
        ts = base_time + timedelta(milliseconds=i * random.randint(50, 200))
        if random.random() < anomaly_rate:
            rows.append(_anomaly_row(ts))
        else:
            rows.append(_normal_row(ts))

    return rows


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate synthetic network traffic CSV"
    )
    parser.add_argument("--rows", type=int, default=1000, help="Number of rows")
    parser.add_argument(
        "--anomaly-rate", type=float, default=0.05, help="Fraction of anomalous rows"
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument(
        "--output", type=str, default="network_traffic.csv", help="Output file"
    )
    args = parser.parse_args()

    rows = generate(args.rows, args.anomaly_rate, args.seed)
    out_path = Path(__file__).parent / args.output
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[OK] Generated {len(rows)} rows -> {out_path}")


if __name__ == "__main__":
    main()
