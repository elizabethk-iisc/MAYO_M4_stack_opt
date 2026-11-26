#!/usr/bin/env python3
"""
Flash an ELF to the Nucleo-L4R5ZI with OpenOCD and show the board's serial output.

Opens the ST-LINK virtual COM port (like `picocom -b 38400 /dev/ttyACM0`),
runs OpenOCD, prints only the key OpenOCD progress lines, then prints
everything the board sends after reset until pqm4's end marker '#'
(or a timeout), and exits.

Only uses the Python standard library (no pyserial needed).
"""

import argparse
import os
import select
import subprocess
import sys
import termios
import threading
import time

BAUDS = {
    9600: termios.B9600,
    19200: termios.B19200,
    38400: termios.B38400,
    57600: termios.B57600,
    115200: termios.B115200,
    230400: termios.B230400,
}

# OpenOCD lines worth showing
KEEP = (
    "Programming Started",
    "Programming Finished",
    "Verify Started",
    "Verified OK",
    "Resetting Target",
)


def open_serial(port, baud):
    """Open the serial port in raw 8N1 mode at the given baud rate."""
    fd = os.open(port, os.O_RDONLY | os.O_NOCTTY | os.O_NONBLOCK)
    attrs = termios.tcgetattr(fd)
    cc = attrs[6]
    cc[termios.VMIN] = 0
    cc[termios.VTIME] = 0
    speed = BAUDS[baud]
    termios.tcsetattr(
        fd,
        termios.TCSANOW,
        [
            0,                                              # iflag: raw
            0,                                              # oflag: raw
            termios.CS8 | termios.CREAD | termios.CLOCAL,   # cflag: 8N1
            0,                                              # lflag: no echo/canonical
            speed,
            speed,
            cc,
        ],
    )
    termios.tcflush(fd, termios.TCIFLUSH)
    return fd


class SerialReader(threading.Thread):
    """Reads the serial port in the background; prints only once capture is enabled."""

    def __init__(self, fd, end_marker):
        super().__init__(daemon=True)
        self.fd = fd
        self.end_marker = end_marker
        self.capture = threading.Event()  # set when the board is reset
        self.done = threading.Event()     # set when the end marker arrives
        self.stop = threading.Event()

    def run(self):
        while not self.stop.is_set():
            ready, _, _ = select.select([self.fd], [], [], 0.1)
            if not ready:
                continue
            try:
                data = os.read(self.fd, 4096)
            except (BlockingIOError, InterruptedError):
                continue
            if not data or not self.capture.is_set():
                continue  # discard anything from before the reset
            text = data.decode(errors="replace")
            if self.end_marker and self.end_marker in text:
                sys.stdout.write(text.split(self.end_marker, 1)[0])
                sys.stdout.flush()
                self.done.set()
                return
            sys.stdout.write(text)
            sys.stdout.flush()


def main():
    p = argparse.ArgumentParser(description="Flash Nucleo-L4R5ZI and show serial output.")
    p.add_argument("elf", help="ELF file to flash (required)")
    p.add_argument("--cfg", default="st_nucleo_l4r5.cfg", help="OpenOCD config (default: %(default)s)")
    p.add_argument("--port", default="/dev/ttyACM0", help="serial port (default: %(default)s)")
    p.add_argument("--baud", type=int, default=38400, choices=sorted(BAUDS),
                   help="baud rate (default: %(default)s)")
    p.add_argument("--timeout", type=float, default=120,
                   help="seconds to wait for output after reset (default: %(default)s)")
    p.add_argument("--end-marker", default="#",
                   help="stop when this appears in the output; '' to wait for timeout (default: '#')")
    args = p.parse_args()

    if not os.path.isfile(args.elf):
        sys.exit(f"ELF not found: {args.elf}")

    try:
        fd = open_serial(args.port, args.baud)
    except OSError as e:
        sys.exit(f"Could not open {args.port}: {e}")

    reader = SerialReader(fd, args.end_marker)
    reader.start()

    cmd = ["openocd", "-f", args.cfg, "-c", f"program {args.elf} verify reset exit"]
    log = []
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, bufsize=1)
    except FileNotFoundError:
        sys.exit("openocd not found - install it with: sudo apt install openocd")

    for line in proc.stdout:
        line = line.rstrip()
        log.append(line)
        if any(k in line for k in KEEP):
            print(line, flush=True)
            if "Resetting Target" in line:
                reader.capture.set()  # board is about to start the new firmware
    proc.wait()

    if proc.returncode != 0 or not reader.capture.is_set():
        print("\nOpenOCD failed. Full output:\n" + "\n".join(log), file=sys.stderr)
        reader.stop.set()
        os.close(fd)
        sys.exit(1)

    print("\n--- board output ---", flush=True)
    finished = reader.done.wait(timeout=args.timeout)
    reader.stop.set()
    reader.join(timeout=1)
    os.close(fd)

    if args.end_marker and not finished:
        print(f"\n--- timed out after {args.timeout:.0f}s without seeing '{args.end_marker}' ---")
    else:
        print("\n--- done ---")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted.")
