# Memory-Optimized MAYO for ARM Cortex-M4

A stack-optimized implementation of the **MAYO** post-quantum signature scheme for ARM Cortex-M4 microcontrollers. The code follows the PQM4 directory layout.
Test files are present in mupq/crypto_sign.

## Building

### Usage

```bash
python3 build_mayo.py <MAYO version> [v1|v2] [test|speed|stack] [--dry-run]
```

Everything after the MAYO version is optional and can be given in any order. Options are case-insensitive.

| Input | Values | Default |
|---|---|---|
| MAYO version | `1`, `2`, `3`, `5` (or `mayo1`, `mayo2`, …) | prompts if omitted |
| Variant | `v1`, `v2` | `v1` |
| Program | `test`, `speed`, `stack` | `test` |

`--dry-run` prints the full gcc command without running it, so you can check what would be built.

When the variant or program is left out, the script prints a note saying which default it used.

### Examples

```bash
python3 build_mayo.py 2               # MAYO2, v1, test
python3 build_mayo.py 2 v2            # MAYO2, v2, test
python3 build_mayo.py 2 v2 speed      # MAYO2, v2, speed
python3 build_mayo.py 3 stack         # MAYO3, v1, stack
python3 build_mayo.py mayo5 stack v2  # MAYO5, v2, stack
python3 build_mayo.py                 # asks for the MAYO version
python3 build_mayo.py 1 v2 speed --dry-run   # show the command only
```

### Output

The ELF is written to `elf/` (created if missing):

```
elf/crypto_sign_mayo<N>_opt_<program>.elf
```

For example, `elf/crypto_sign_mayo2_opt_speed.elf`. Note that v1 and v2 builds of the same version and program share a file name, so a v2 build overwrites the matching v1 ELF.


## Running in QEMU

```bash
qemu-system-arm -M mps2-an386 -nographic -semihosting \
  -kernel elf/crypto_sign_mayo<N>_opt_<program>.elf
```
