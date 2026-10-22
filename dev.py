"""
UtsavAI Development Server Launcher.

Displays clickable Local (Laptop) and Network (Phone) links,
then starts Uvicorn with auto-reload bound to 0.0.0.0.
"""

from __future__ import annotations

import contextlib
import os
import socket
import subprocess
import sys

# Configure UTF-8 encoding for Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    with contextlib.suppress(Exception):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def get_network_ip() -> str | None:
    """Detect local network IPv4 address (e.g. 192.168.1.x)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return str(ip)
    except Exception:
        return None


def is_port_in_use(port: int) -> bool:
    """Check if a port is already occupied on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        return s.connect_ex(("127.0.0.1", port)) == 0


def select_port(preferred: int = 8000) -> int:
    """Use preferred port if free, or find next free port."""
    if not is_port_in_use(preferred):
        return preferred
    for p in range(preferred + 1, preferred + 20):
        if not is_port_in_use(p):
            return p
    return preferred


def print_banner(port: int, network_ip: str | None, port_shifted: bool = False) -> None:
    """Print clean dev server banner with Laptop and Phone links."""
    cyan = "\033[96m"
    green = "\033[92m"
    yellow = "\033[93m"
    bold = "\033[1m"
    dim = "\033[2m"
    reset = "\033[0m"

    if os.name == "nt":
        os.system("")

    print()
    print(f"{bold}{cyan}  ✦ UtsavAI Event Planner{reset} {dim}v1.0.0{reset}")
    if port_shifted:
        print(f"  {yellow}⚠  Port 8000 already in use, running on port {port} instead.{reset}")
    print()
    print(
        f"  {green}➜{reset}  {bold}Local (Laptop):{reset}   {cyan}http://localhost:{port}/{reset}"
    )
    if network_ip:
        print(
            f"  {green}➜{reset}  {bold}Network (Phone):{reset}  {cyan}http://{network_ip}:{port}/{reset}"
        )
    else:
        print(
            f"  {yellow}➜{reset}  {dim}Network (Phone):  Not connected to Wi-Fi / Local Network{reset}"
        )
    print()
    print(
        f"  {dim}💡 Phone me chalane ke liye Phone aur Laptop same Wi-Fi se connect hone chahiye.{reset}"
    )
    print(f"  {dim}Press Ctrl+C to stop server.{reset}")
    print()


def main() -> None:
    """Launch UtsavAI development server on preferred or available port."""
    preferred_port = int(os.getenv("PORT", "8000"))
    port = select_port(preferred_port)
    port_shifted = port != preferred_port
    host = "0.0.0.0"
    network_ip = get_network_ip()

    print_banner(port, network_ip, port_shifted)

    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "backend.main:app",
        "--reload",
        "--host",
        host,
        "--port",
        str(port),
    ]

    try:
        subprocess.run(cmd, check=False)
    except KeyboardInterrupt:
        print("\nServer stopped.")


if __name__ == "__main__":
    main()
