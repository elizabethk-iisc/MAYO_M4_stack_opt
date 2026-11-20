#!/usr/bin/env python3
"""
Build the pqm4 MAYO reference test ELF for a chosen MAYO version.

Usage:
    python3 build_mayo.py 2          # build MAYO2
    python3 build_mayo.py mayo3      # also accepted
    python3 build_mayo.py            # prompts for the version
    python3 build_mayo.py 5 --dry-run   # print the command without running it
"""

import argparse
import os
import shlex
import subprocess
import sys

SUPPORTED = ("1", "2", "3", "5")

CPU_FLAGS = [
    "-mcpu=cortex-m4", "-mthumb", "-mfloat-abi=hard", "-mfpu=fpv4-sp-d16",
]

WRAPPED_SYSCALLS = [
    "_sbrk", "_open", "_close", "_isatty", "_kill", "_lseek",
    "_read", "_write", "_fstat", "_getpid",
]

COMMON_SOURCES = [
    "mupq/crypto_sign/test.c",
    "mupq/common/fips202.c",
    "mupq/common/sp800-185.c",
    "mupq/common/nistseedexpander.c",
    "common/keccakf1600.S",
    "common/aes.c",
    "common/aes-encrypt.S",
    "common/aes-keyschedule.S",
    "common/aes-publicinputs.c",
    "common/aes-publicinputs.S",
    "mupq/common/sha2.c",
    "common/crypto_hashblocks_sha512_inner32.s",
    "common/crypto_hashblocks_sha512.c",
]

MAYO_SOURCES = ["aes_ctr.c", "api.c", "arithmetic.c", "mayo.c", "mem.c", "params.c"]


def build_command(version: str) -> list[str]:
    impl_dir = f"mayo{version}"
    output = f"elf/crypto_sign_mayo{version}_ref_test.elf"

    cmd = ["arm-none-eabi-gcc"]
    cmd += CPU_FLAGS
    cmd += [
        "-std=gnu99", "--sysroot=",
        "-I./common", "-I./mupq/common",
        "-O3", "-g3", "-Wall", "-Wextra", "-Wshadow", "-MMD", "-fno-common",
        "-DMPS2_AN386", "-DMUPQ", "-DMUPQ_NAMESPACE=", "-DMUPQ_ITERATIONS=1",
        "-DMUPQ_MAXMLEN=2048", "-DPQM4",
        f"-I./{impl_dir}",
        "--specs=nosys.specs",
    ]
    cmd += [f"-Wl,--wrap={s}" for s in WRAPPED_SYSCALLS]
    cmd += ["-Wl,--no-warn-rwx-segments", "-ffreestanding", "-Tobj/ldscript.ld"]
    cmd += CPU_FLAGS
    cmd += ["-Lobj", "-Wl,--gc-sections", "-o", output]
    cmd += COMMON_SOURCES
    cmd += [f"{impl_dir}/{src}" for src in MAYO_SOURCES]
    cmd += ["-Wl,--start-group", "-lpqm4hal", "-lm", "-Wl,--end-group"]
    return cmd


def normalize_version(raw: str) -> str:
    v = raw.strip().lower().removeprefix("mayo").strip("_- ")
    if v not in SUPPORTED:
        sys.exit(f"Unsupported MAYO version '{raw}'. Choose one of: {', '.join(SUPPORTED)}")
    return v


def main() -> None:
    parser = argparse.ArgumentParser(description="Build pqm4 MAYO reference test ELF.")
    parser.add_argument("version", nargs="?", help="MAYO version: 1, 2, 3 or 5")
    parser.add_argument("--dry-run", action="store_true",
                        help="print the command without running it")
    args = parser.parse_args()

    raw = args.version or input(f"Enter MAYO version ({'/'.join(SUPPORTED)}): ")
    version = normalize_version(raw)
    cmd = build_command(version)

    print(f"==> Building MAYO{version}")
    print(shlex.join(cmd), "\n")

    if args.dry_run:
        return

    if not os.path.isdir(f"mayo{version}"):
        sys.exit(f"Directory mayo{version} not found — run this from the pqm4 build root.")
    os.makedirs("elf", exist_ok=True)

    try:
        result = subprocess.run(cmd)
    except FileNotFoundError:
        sys.exit("arm-none-eabi-gcc not found on PATH.")

    if result.returncode == 0:
        print(f"\nSuccess: elf/crypto_sign_mayo{version}_ref_test.elf")
    else:
        print(f"\nBuild failed (exit code {result.returncode}).")
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
