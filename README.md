# Memory-Optimized MAYO for ARM Cortex-M4

A stack-optimized implementation of the **MAYO** post-quantum signature scheme for ARM Cortex-M4 microcontrollers. The code follows the PQM4 directory layout.
Test files are present in mupq/crypto_sign.

## Building

The command below compiles the test binary for **MAYO_1**. For another parameter set, replace every `mayo1` with that set's name (for example `mayo2`).

```bash
arm-none-eabi-gcc \
  -mcpu=cortex-m4 -mthumb -mfloat-abi=hard -mfpu=fpv4-sp-d16 \
  -std=gnu99 --sysroot= -O3 -g3 \
  -Wall -Wextra -Wshadow -MMD -fno-common -ffreestanding \
  -I./common -I./mupq/common -I./mayo1/ref \
  -DMPS2_AN386 -DMUPQ -DMUPQ_NAMESPACE= -DMUPQ_ITERATIONS=1 \
  -DMUPQ_MAXMLEN=2048 -DPQM4 \
  --specs=nosys.specs \
  -Wl,--wrap=_sbrk -Wl,--wrap=_open -Wl,--wrap=_close -Wl,--wrap=_isatty \
  -Wl,--wrap=_kill -Wl,--wrap=_lseek -Wl,--wrap=_read -Wl,--wrap=_write \
  -Wl,--wrap=_fstat -Wl,--wrap=_getpid -Wl,--no-warn-rwx-segments \
  -Tobj/ldscript.ld -Lobj -Wl,--gc-sections \
  -o elf/crypto_sign_mayo1_ref_test.elf \
  mupq/crypto_sign/test.c \
  mupq/common/fips202.c mupq/common/sp800-185.c \
  mupq/common/nistseedexpander.c mupq/common/sha2.c \
  common/keccakf1600.S \
  common/aes.c common/aes-encrypt.S common/aes-keyschedule.S \
  common/aes-publicinputs.c common/aes-publicinputs.S \
  common/crypto_hashblocks_sha512_inner32.s common/crypto_hashblocks_sha512.c \
  mayo1/ref/aes_ctr.c mayo1/ref/api.c mayo1/ref/arithmetic.c \
  mayo1/ref/mayo.c mayo1/ref/mem.c mayo1/ref/params.c \
  -Wl,--start-group -lpqm4hal -lm -Wl,--end-group
```

## Running in QEMU

```bash
qemu-system-arm -M mps2-an386 -nographic -semihosting \
  -kernel elf/crypto_sign_mayo1_ref_test.elf
```
