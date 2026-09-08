# TestRepo

This repository contains a small utility script that prints the system uptime in a human-readable format.

## Files

- `copilot_test.py` — Script that detects the platform and prints system uptime (supports Windows, Linux, macOS fallbacks).

## How to run

1. From the repository root, run the script with Python 3:

```bash
python3 copilot_test.py
```

2. Or make it executable and run directly:

```bash
chmod +x copilot_test.py
./copilot_test.py
```

3. If you prefer to use psutil (recommended for reliability), install it first:

```bash
pip install psutil
python3 copilot_test.py
```

## Expected outcome

- The script prints the detected platform and the system uptime in one of these formats:

  - When uptime is less than a day:

    Platform detected: Linux
    System uptime: 03:12:45

  - When uptime includes days:

    Platform detected: Windows
    System uptime: 2 days, 05:23:12

- Exit codes:
  - `0` — uptime printed successfully
  - `1` — could not determine uptime on this platform
  - `2` — an unexpected error occurred while determining uptime

## Implementation details (short)

- The script prefers `psutil.boot_time()` if `psutil` is installed.
- Linux: reads `/proc/uptime` if available.
- Windows: uses `GetTickCount64` via `ctypes`.
- macOS: attempts `sysctl -n kern.boottime` or `uptime -s`.
- Generic fallback: `uptime -s` to get boot time and compute uptime.
- All external commands use `subprocess.run()` (no `os.popen` or `shell=True`).

## Pitfalls and notes

- psutil is the most reliable method; without it, the script relies on platform-specific fallbacks which may fail on unusual or locked-down systems.

- `uptime -s` may not be available on very old Unix systems or minimal containers; in that case the script tries other fallbacks but may still be unable to determine uptime.

- Timezone/parsing: when parsing the output of `uptime -s`, the script tries several common datetime formats. If your system prints an uncommon format, boot-time parsing may fail and the script will fall back or exit with code `1`.

- Windows accuracy: `GetTickCount64` reports milliseconds since the system booted and is generally accurate; it does not wrap like `GetTickCount` (32-bit), but some virtualization/hypervisor scenarios can affect perceived uptime.

- Permission/sandboxing: reading `/proc/uptime` usually requires no special permissions, but restricted container environments or sandboxes may restrict access to necessary files/commands.

## Next suggestions

- If you want machine-readable output (JSON or raw seconds), I can add a CLI with `argparse` and `--json`/`--seconds` flags.
- If you rely on `psutil`, consider adding a `requirements.txt` or `pyproject.toml` entry so CI and users install it automatically.

