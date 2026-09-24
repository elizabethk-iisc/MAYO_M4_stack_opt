// SPDX-License-Identifier: Apache-2.0

#ifndef AESCTR_H
#define AESCTR_H

#include <stddef.h>
#include <stdint.h>

void AES_256_ECB(const uint8_t *input, const uint8_t *key, uint8_t *output);

/* AES-128 ECB over whole blocks. The portable and AES-NI implementations agree
   block for block, so the lambda keystream is backend independent. */
int AES_128_ECB_C(unsigned char *output, const unsigned char *input, size_t nblocks,
                  const unsigned char *key);
#ifdef ENABLE_AESNI
int AES_128_ECB_NI(unsigned char *output, const unsigned char *input, size_t nblocks,
                   const unsigned char *key);
#define AES_128_ECB AES_128_ECB_NI
#else
#define AES_128_ECB AES_128_ECB_C
#endif
#define AES_ECB_encrypt AES_256_ECB

#ifdef ENABLE_AESNI
int AES_128_CTR_NI(unsigned char *output, size_t outputByteLen,
                   const unsigned char *input, size_t inputByteLen);
int AES_128_CTR_4R_NI(unsigned char *output, size_t outputByteLen,
                      const unsigned char *input, size_t inputByteLen);
#define AES_128_CTR AES_128_CTR_NI
#else
#ifdef ENABLE_AESNEON
int AES_128_CTR_NEON(unsigned char *output, size_t outputByteLen,
                   const unsigned char *input, size_t inputByteLen);
int AES_128_CTR_4R_NI(unsigned char *output, size_t outputByteLen,
                      const unsigned char *input, size_t inputByteLen);
#define AES_128_CTR AES_128_CTR_NEON
#else
int AES_128_CTR(unsigned char *output, size_t outputByteLen,
                const unsigned char *input, size_t inputByteLen);
#endif
#endif

typedef struct {
    unsigned char buf[16];

    uint32_t ivw[4];

    const uint64_t *rkeys;

    void (*aes_encrypt_asm)(const uint8_t *,
                            const uint8_t *,
                            uint8_t *);

    size_t pos;
    size_t available;
} aes_ctr_stream_t;

/* AES CTR stream functions */
void aes_ctr_init(aes_ctr_stream_t *s, const unsigned char *iv, uint32_t counter, const uint64_t *rkeys, 
                  void (*aes_encrypt_asm)(const uint8_t *, const uint8_t *, uint8_t *));

void aes_ctr_refill(aes_ctr_stream_t *s);

void aes_ctr_get_words(aes_ctr_stream_t *s, uint64_t *out, size_t nbytes);

#endif

