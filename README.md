# Memory-Optimized MAYO for ARM Cortex-M4

A stack-optimized implementation of the **MAYO** post-quantum signature scheme for ARM Cortex-M4 microcontrollers. The code follows the PQM4 directory layout.
Test files are present in mupq/crypto_sign.

# Building

There are two build scripts, one per target:

```bash
# NUCLEO-L4R5ZI board
python3 build_mayo_nucleo.py <MAYO version> [v1|v2] [test|speed|stack] [--dry-run]

# QEMU (mps2-an386)
python3 build_mayo_qemu.py <MAYO version> [v1|v2] [test|speed|stack] [--dry-run]
```

### Usage

Both scripts take the same inputs. Everything after the MAYO version is optional and can be given in any order. Options are case-insensitive.

| Input | Values | Default |
|---|---|---|
| MAYO version | `1`, `2`, `3`, `5` (or `mayo1`, `mayo2`, …) | prompts if omitted |
| Variant | `v1`, `v2` | `v1` |
| Program | `test`, `speed`, `stack` | `test` |

`--dry-run` prints the full gcc command without running it, so you can check what would be built.

When the variant or program is left out, the script prints a note saying which default it used.

### Examples

```bash
python3 build_mayo_nucleo.py 2               # MAYO2, v1, test
python3 build_mayo_nucleo.py 2 v2 speed      # MAYO2, v2, speed
python3 build_mayo_nucleo.py 3 stack         # MAYO3, v1, stack
```

The same examples work with `build_mayo_qemu.py`.

### Output

The ELF is written to `elf/` (created if missing):

```
elf/crypto_sign_mayo<N>_opt_<program>.elf
```

For example, `elf/crypto_sign_mayo2_opt_speed.elf`. Note that both scripts, and v1 and v2 builds of the same version and program, share a file name, so a new build overwrites the previous ELF.

# Running the ELF

### Running on the Nucleo board

```bash
python3 flash_and_run.py elf/crypto_sign_mayo<N>_opt_<program>.elf [--baud <rate>] [--port <device>] [--cfg <file>]
```

The optional settings are:

- `--baud`: serial speed (default `38400`). It must match the firmware's `SERIAL_BAUD`, e.g. `--baud 115200`.
- `--port`: serial device (default `/dev/ttyACM0`), e.g. `--port /dev/ttyACM1` when two boards are plugged in.
- `--cfg`: OpenOCD config file (default `st_nucleo_l4r5.cfg`), for a different board or a config stored elsewhere.

### Running on QEMU

```bash
qemu-system-arm -M mps2-an386 -nographic -semihosting -kernel elf/crypto_sign_mayo<N>_opt_<program>.elf
```
