#!/usr/bin/env python3
"""
copilot_test.py

Improved system uptime reporter with clear platform-specific flows, safer subprocess usage,
and structured functions with exception handling for Windows and Linux (plus macOS/fallbacks).

Usage:
  python3 copilot_test.py

Behavior:
  - Detects platform at startup and uses the appropriate code path.
  - Uses psutil when available for a reliable boot time.
  - Avoids os.popen; uses subprocess.run with check and capture_output.
  - Returns uptime in seconds; formats human-readable output.
"""
from __future__ import annotations

import ctypes
import datetime
import os
import platform
import re
import subprocess
import time
from typing import List, Optional


def format_duration(seconds: float) -> str:
    """Format a duration in seconds as "N day(s), HH:MM:SS" or "HH:MM:SS".

    Rounds down to whole seconds.
    """
    seconds = int(max(0, int(seconds)))
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    hhmmss = f"{hours:02d}:{minutes:02d}:{secs:02d}"
    if days:
        return f"{days} day{'s' if days != 1 else ''}, {hhmmss}"
    return hhmmss


def run_command(cmd: List[str], *, timeout: float = 5.0) -> Optional[str]:
    """Run a command securely and return stdout (stripped) on success, or None on failure.

    Uses subprocess.run with capture_output and text mode. Does not shell-expand input.
    """
    try:
        completed = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=timeout)
        return completed.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return None


def get_uptime_psutil() -> Optional[float]:
    """Try to get uptime using psutil if it's available.

    Returns uptime in seconds or None.
    """
    try:
        import psutil  # type: ignore

        boot = psutil.boot_time()
        return time.time() - float(boot)
    except Exception:
        return None


def get_uptime_windows() -> Optional[float]:
    """Windows-specific uptime using GetTickCount64 (milliseconds since boot).

    Returns seconds or None.
    """
    try:
        GetTickCount64 = ctypes.windll.kernel32.GetTickCount64
        GetTickCount64.restype = ctypes.c_ulonglong
        ms = GetTickCount64()
        return float(ms) / 1000.0
    except Exception:
        return None


def get_uptime_proc() -> Optional[float]:
    """Linux: read /proc/uptime if available.

    Returns seconds or None.
    """
    try:
        if os.path.exists("/proc/uptime"):
            with open("/proc/uptime", "r", encoding="utf-8") as f:
                contents = f.read().strip().split()
                if contents:
                    return float(contents[0])
    except Exception:
        return None
    return None


def parse_boot_time_from_uptime_s(output: str) -> Optional[float]:
    """Parse output of `uptime -s` (boot time) into seconds since epoch.

    Supports common datetime formats produced by uptime on many Linux/macOS systems.
    """
    if not output:
        return None
    # Try several common formats
    fmts = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S")
    for fmt in fmts:
        try:
            dt = datetime.datetime.strptime(output, fmt)
            # If no tz info, assume local time
            if dt.tzinfo is None:
                return dt.timestamp()
            return dt.timestamp()
        except Exception:
            continue
    return None


def get_uptime_using_uptime_s() -> Optional[float]:
    """Use `uptime -s` to get boot time, then compute uptime in seconds."""
    out = run_command(["uptime", "-s"])  # boot time string
    if not out:
        return None
    boot_ts = parse_boot_time_from_uptime_s(out)
    if boot_ts is None:
        return None
    return time.time() - boot_ts


def get_uptime_macos() -> Optional[float]:
    """macOS-specific method using sysctl kern.boottime or fallback to uptime -s."""
    # Try sysctl -n kern.boottime which may return something like: { sec = 1600000000, usec = 0 }
    out = run_command(["sysctl", "-n", "kern.boottime"]) or ""
    if out:
        m = re.search(r"sec\s*=\s*(\d+)", out)
        if m:
            try:
                boot = int(m.group(1))
                return time.time() - float(boot)
            except Exception:
                pass
    # Fallback to uptime -s
    return get_uptime_using_uptime_s()


def get_uptime_generic() -> Optional[float]:
    """Generic fallback: try uptime -s then return None if unavailable."""
    return get_uptime_using_uptime_s()


def get_system_uptime_seconds() -> Optional[float]:
    """Top-level function to determine system uptime in seconds using multiple strategies.

    Tries, in order:
      1. psutil
      2. Platform-specific fast paths (Windows/GetTickCount64, /proc/uptime)
      3. macOS sysctl
      4. uptime -s (generic)

    Returns seconds or None if all strategies fail.
    """
    # 1. psutil
    v = get_uptime_psutil()
    if v is not None:
        return v

    system = platform.system()

    # 2. platform fast-paths
    if system == "Windows":
        v = get_uptime_windows()
        if v is not None:
            return v

    # POSIX /proc path (Linux and some other UNIX)
    v = get_uptime_proc()
    if v is not None:
        return v

    # macOS-specific
    if system == "Darwin":
        v = get_uptime_macos()
        if v is not None:
            return v

    # Generic fallback using uptime -s
    v = get_uptime_generic()
    if v is not None:
        return v

    return None


def main() -> int:
    try:
        system = platform.system()
        uptime_seconds = get_system_uptime_seconds()
        if uptime_seconds is None or uptime_seconds <= 0:
            print(f"Platform detected: {system}")
            print("Could not determine system uptime on this platform.")
            return 1

        print(f"Platform detected: {system}")
        print("System uptime:", format_duration(uptime_seconds))
        return 0
    except Exception as exc:  # top-level safety net
        print("An unexpected error occurred while determining uptime:", str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
