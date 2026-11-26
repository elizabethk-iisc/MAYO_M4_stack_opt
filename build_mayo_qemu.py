#!/usr/bin/env python3
"""
Build a pqm4 MAYO ELF (test, speed or stack) for a chosen MAYO version.

Usage:
    python3 build_mayo.py 2               # MAYO2, v1, test (defaults)
    python3 build_mayo.py 2 v2            # MAYO2 with -DMAYO_OPT_V2, test
    python3 build_mayo.py 2 v2 speed      # MAYO2, v2, mupq/crypto_sign/speed.c
    python3 build_mayo.py 3 stack         # MAYO3, v1, mupq/crypto_sign/stack.c
    python3 build_mayo.py mayo5 stack v2  # v1/v2 and test/speed/stack in any order
    python3 build_mayo.py                 # prompts for the MAYO version
    python3 build_mayo.py 5 v2 speed --dry-run   # print the command without running it
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

OPTS = ("v1", "v2")
PROGRAMS = ("test", "speed", "stack")

COMMON_SOURCES = [
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


def output_path(version: str, program: str) -> str:
    return f"elf/crypto_sign_mayo{version}_opt_{program}.elf"


def build_command(version: str, opt: str = "v1", program: str = "test") -> list[str]:
    impl_dir = f"mayo{version}"
    output = output_path(version, program)

    cmd = ["arm-none-eabi-gcc"]
    cmd += CPU_FLAGS
    cmd += [
        "-std=gnu99", "--sysroot=",
        "-I./common", "-I./mupq/common",
        "-O3", "-g3", "-Wall", "-Wextra", "-Wshadow", "-MMD", "-fno-common",
        "-DMPS2_AN386", "-DMUPQ", "-DMUPQ_NAMESPACE=", "-DMUPQ_ITERATIONS=1",
        "-DMUPQ_MAXMLEN=2048", "-DPQM4",
    ]
    if opt == "v2":
        # Command-line define: visible to every .c file and every .h it includes
        cmd.append("-DMAYO_OPT_V2")
    cmd += [
        f"-I./{impl_dir}",
        "--specs=nosys.specs",
    ]
    cmd += [f"-Wl,--wrap={s}" for s in WRAPPED_SYSCALLS]
    cmd += ["-Wl,--no-warn-rwx-segments", "-ffreestanding", "-Tobj_qemu/ldscript.ld"]
    cmd += CPU_FLAGS
    cmd += ["-Lobj_qemu", "-Wl,--gc-sections", "-o", output]
    cmd += [f"mupq/crypto_sign/{program}.c"]
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
    parser.add_argument("options", nargs="*", metavar="OPTION",
                        help="any of: v1 (default) or v2 (adds -DMAYO_OPT_V2); "
                             "test (default), speed or stack — in any order")
    parser.add_argument("--dry-run", action="store_true",
                        help="print the command without running it")
    args = parser.parse_args()

    raw = args.version or input(f"Enter MAYO version ({'/'.join(SUPPORTED)}): ")
    version = normalize_version(raw)

    opt = None
    program = None
    for item in (o.lower() for o in args.options):
        if item in OPTS:
            if opt is not None and opt != item:
                parser.error(f"conflicting variants: {opt} and {item}")
            opt = item
        elif item in PROGRAMS:
            if program is not None and program != item:
                parser.error(f"conflicting programs: {program} and {item}")
            program = item
        else:
            parser.error(f"unknown option '{item}' "
                         f"(expected one of: {', '.join(OPTS + PROGRAMS)})")

    if opt is None:
        print("No version (v1/v2) specified, so running v1 by default.")
        opt = "v1"
    if program is None:
        print("No program (test/speed/stack) specified, so running test by default.")
        program = "test"

    cmd = build_command(version, opt, program)

    print(f"==> Building MAYO{version} ({opt}, {program})")
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
        print(f"\nSuccess: {output_path(version, program)}")
    else:
        print(f"\nBuild failed (exit code {result.returncode}).")
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
