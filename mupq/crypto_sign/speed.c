// SPDX-License-Identifier: Apache-2.0 or CC0-1.0
#include "api.h"
#include "hal.h"
#include "sendfn.h"
#include "randombytes.h"

#include <stdio.h>
#include <stdint.h>
#include <string.h>

#include <mayo.h>

#define MLEN 59

// https://stackoverflow.com/a/1489985/1711232
#define PASTER(x, y) x##y
#define EVALUATOR(x, y) PASTER(x, y)
#define NAMESPACE(fun) EVALUATOR(MUPQ_NAMESPACE, fun)

// use different names so we can have empty namespaces
#define MUPQ_CRYPTO_PUBLICKEYBYTES NAMESPACE(CRYPTO_PUBLICKEYBYTES)
#define MUPQ_CRYPTO_SECRETKEYBYTES NAMESPACE(CRYPTO_SECRETKEYBYTES)
#define MUPQ_CRYPTO_BYTES          NAMESPACE(CRYPTO_BYTES)
#define MUPQ_CRYPTO_ALGNAME        NAMESPACE(CRYPTO_ALGNAME)

#define MUPQ_crypto_sign_keypair NAMESPACE(crypto_sign_keypair)
#define MUPQ_crypto_sign NAMESPACE(crypto_sign)
#define MUPQ_crypto_sign_open NAMESPACE(crypto_sign_open)
#define MUPQ_crypto_sign_signature NAMESPACE(crypto_sign_signature)
#define MUPQ_crypto_sign_verify NAMESPACE(crypto_sign_verify)

#define printcycles(S, U) send_unsignedll((S), (U))

void bench_esk(unsigned char *sk, unsigned char *sm, size_t *smlen)
{
  unsigned long long t0, t1;
  sk_t xsk;
  t0 = hal_get_time();
  (void) mayo_expand_sk(0, sk, &xsk);
  t1 = hal_get_time();
  printcycles("expand_sk cycles:", t1-t0);

  randombytes(sm, MLEN);
  t0 = hal_get_time();
  (void) mayo_sign_esk(0, sm, smlen, sm, MLEN, &xsk);
  t1 = hal_get_time();
  printcycles("sign_esk cycles:", t1-t0);
}

void bench_epk(unsigned char *pk, unsigned char *sm, size_t smlen)
{
  unsigned long long t0, t1;
  size_t mlen;
  pk_t xpk;
  t0 = hal_get_time();
  (void) mayo_expand_pk(0, pk, xpk.p);
  t1 = hal_get_time();
  printcycles("expand_pk cycles:", t1-t0);

  t0 = hal_get_time();
  (void) mayo_open_epk(0, sm, &mlen, sm, smlen, xpk.p);
  t1 = hal_get_time();
  printcycles("verify_epk cycles:", t1-t0);
}

int main(void)
{
  unsigned char sk[MUPQ_CRYPTO_SECRETKEYBYTES];
  unsigned char pk[MUPQ_CRYPTO_PUBLICKEYBYTES];
  unsigned char sm[MLEN+MUPQ_CRYPTO_BYTES];
  size_t smlen;
  unsigned long long t0, t1;
  int i;

  hal_setup(CLOCK_BENCHMARK);

  hal_send_str("==========================");

  for(i=0;i<MUPQ_ITERATIONS; i++)
  {
    // Key-pair generation
    t0 = hal_get_time();
    MUPQ_crypto_sign_keypair(pk, sk);
    t1 = hal_get_time();
    printcycles("keypair cycles:", t1-t0);

    // ExpandSK and Sign from the expanded key
    bench_esk(sk, sm, &smlen);
    // ExpandPK and Verify from the expanded key, on the signature just produced
    bench_epk(pk, sm, smlen);

    // Signing
    randombytes(sm, MLEN);
    t0 = hal_get_time();
    MUPQ_crypto_sign(sm, &smlen, sm, MLEN, sk);
    t1 = hal_get_time();
    printcycles("sign cycles:", t1-t0);

    // Verification
    t0 = hal_get_time();
    MUPQ_crypto_sign_open(sm, &smlen, sm, smlen, pk);
    t1 = hal_get_time();
    printcycles("verify cycles:", t1-t0);

    hal_send_str("+");
  }
  hal_send_str("#");
  return 0;
}
