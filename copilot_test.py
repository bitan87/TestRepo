#!/usr/bin/env python3
"""
copilot_test.py

Print system uptime in a human-readable form.
Tries psutil first, then platform-specific fallbacks for Linux, macOS, and Windows.
"""
import time
import os
import platform
import subprocess
import ctypes


def format_duration(seconds: float) -> str:
    seconds = int(seconds)
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    parts = []
    if days:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    parts.append(f"{hours:02d}:{minutes:02d}:{secs:02d}")
    return ", ".join(parts) if days else parts[0]


def get_uptime_seconds() -> float:
    # Try psutil if available
    try:
        import psutil

        boot = psutil.boot_time()
        return time.time() - boot
    except Exception:
        pass

    system = platform.system()

    # Windows fallback using GetTickCount64
    if system == "Windows":
        try:
            GetTickCount64 = ctypes.windll.kernel32.GetTickCount64
            GetTickCount64.restype = ctypes.c_ulonglong
            ms = GetTickCount64()
            return ms / 1000.0
        except Exception:
            pass

    # POSIX: try /proc/uptime
    if os.path.exists("/proc/uptime"):
        try:
            with open("/proc/uptime", "r") as f:
                content = f.read().strip().split()
                return float(content[0])
        except Exception:
            pass

    # macOS: try sysctl kern.boottime
    if system == "Darwin":
        try:
            out = subprocess.check_output(["sysctl", "-n", "kern.boottime"], text=True)
            # output looks like: { sec = 1600000000, usec = 0 } Fri Sep 13 12:34:56 2020
            import re

            m = re.search(r"sec = (\d+)", out)
            if m:
                boot_sec = int(m.group(1))
                return time.time() - boot_sec
        except Exception:
            pass

    # Generic fallback: try `uptime -s` (boot time)
    try:
        out = subprocess.check_output(["uptime", "-s"], text=True).strip()
        # parse ISO-like datetime if present
        from datetime import datetime

        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S"):
            try:
                boot = datetime.strptime(out, fmt).timestamp()
                return time.time() - boot
            except Exception:
                continue
    except Exception:
        pass

    # Last resort: return 0 and let caller handle it
    return 0.0


def main():
    uptime = get_uptime_seconds()
    if uptime <= 0:
        print("Could not determine system uptime on this platform.")
        return

    print("System uptime:", format_duration(uptime))


if __name__ == "__main__":
    main()
