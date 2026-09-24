#include "aes_ctr.h"
#include "mayo.h"
#include "aes-publicinputs.h"
#include "arithmetic.h"
#include "arithmetic_fixed.h"
#include <string.h>

extern void aes128_encrypt_publicinputs_asm(const uint8_t *rk, const uint8_t *in, uint8_t *out);

static inline uint32_t br_swap32(uint32_t x) {
    x = ((x & (uint32_t)0x00FF00FF) << 8)
        | ((x >> 8) & (uint32_t)0x00FF00FF);
    return (x << 16) | (x >> 16);
}

static inline void inc1_be(uint32_t *x) {
    uint32_t t = br_swap32(*x) + 1;
    *x = br_swap32(t);
}

void aes_ctr_refill(aes_ctr_stream_t *s)
{
    aes128_encrypt_publicinputs_asm(
        (const uint8_t *)s->rkeys,
        (const uint8_t *)s->ivw,
        s->buf
    );

    inc1_be(s->ivw + 3);
    s->pos = 0;
    s->available = 16;
}


void aes_ctr_init(aes_ctr_stream_t *s,
                  const unsigned char *iv,
                  uint32_t counter,
                  const uint64_t *rkeys,
                  void (*aes_encrypt_asm)(const uint8_t *,
                                           const uint8_t *,
                                           uint8_t *))
{
    memset(s->ivw, 0, sizeof(s->ivw));

    memcpy(s->ivw, iv, AESCTR_NONCEBYTES);

    s->ivw[3] = counter;

    s->rkeys = rkeys;
    s->aes_encrypt_asm = aes_encrypt_asm;

    s->pos = 0;
    s->available = 0;
}

void aes_ctr_get_words(aes_ctr_stream_t *s,
                       uint64_t *out,
                       size_t nbytes)
{
    size_t nwords = (nbytes + 7) / 8;

    memset(out, 0, nwords * sizeof(uint64_t));

    for (size_t i = 0; i < nbytes; i++) {

        if (s->available == 0)
            aes_ctr_refill(s);

        out[i >> 3] |=
            (uint64_t)s->buf[s->pos] << (8 * (i & 7));

        s->pos++;
        s->available--;
    }
}

int AES_128_CTR(unsigned char *output, size_t outputByteLen,
                const unsigned char *input, size_t inputByteLen){
    (void) inputByteLen;
    aes128ctx_publicinputs ctx;
    unsigned char iv[12] = {0};
    aes128_ctr_keyexp_publicinputs(&ctx, input);
    aes128_ctr_publicinputs(output, outputByteLen, iv, &ctx);
    return outputByteLen;
}

int AES_128_ECB_C(unsigned char *output, const unsigned char *input, size_t nblocks,
                  const unsigned char *key){
    aes128ctx_publicinputs ctx;
    aes128_ecb_keyexp_publicinputs(&ctx, key);
    aes128_ecb_publicinputs(output, input, nblocks, &ctx);
    return (int)(nblocks * 16);
}
