// SPDX-License-Identifier: BSD-3-Clause
// CPU regression for the arithmetic window in the published R16 patch.
// This is not a framebuffer, macOS loader, or panel simulation.
#include "kern_r16_backlight64.hpp"
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include <sys/mman.h>

static uint64_t checks = 0, arithmeticCases = 0;
static void require(bool value, const char *message) {
    ++checks;
    if (!value) { std::fprintf(stderr, "FAIL: %s\n", message); std::exit(1); }
}

// Independent quotient/remainder oracle: no multiplication of period * raw.
static uint32_t expectedDuty(uint32_t period, uint32_t raw) {
    return uint32_t((period / 65535ULL) * raw + ((period % 65535ULL) * raw) / 65535ULL);
}

class Arithmetic {
    void *memory {};
    size_t length {4096};
public:
    explicit Arithmetic(const uint8_t *window, size_t count) {
        memory = mmap(nullptr, length, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
        require(memory != MAP_FAILED, "mmap generated CPU fixture");
        // SysV ABI adapter: preserve RBX/R14; RBX=controller, R14D=raw.
        const uint8_t prefix[] {0x53,0x41,0x56,0x48,0x89,0xfb,0x41,0x89,0xf6};
        const uint8_t suffix[] {0x89,0xd0,0x41,0x5e,0x5b,0xc3}; // EDX result -> EAX.
        auto *p = static_cast<uint8_t *>(memory);
        std::memcpy(p, prefix, sizeof(prefix));
        std::memcpy(p + sizeof(prefix), window, count);
        std::memcpy(p + sizeof(prefix) + count, suffix, sizeof(suffix));
        require(mprotect(memory, length, PROT_READ | PROT_EXEC) == 0, "fixture executable after writing");
    }
    ~Arithmetic() { if (memory && memory != MAP_FAILED) munmap(memory, length); }
    Arithmetic(const Arithmetic &) = delete;
    uint32_t run(uint32_t period, uint32_t raw) const {
        alignas(16) std::array<uint8_t, 4096> controller {};
        std::memcpy(controller.data() + 0xe60, &period, sizeof(period));
        using Function = uint32_t (*)(void *, uint32_t);
        return reinterpret_cast<Function>(memory)(controller.data(), raw);
    }
};

int main() {
#if !defined(__x86_64__)
    std::fputs("This instruction fixture requires an x86_64 Unix host.\n", stderr);
    return 2;
#endif
    using namespace R16Backlight64;
    Arithmetic oldCode(Original, sizeof(Original)), repairedCode(Repaired, sizeof(Repaired));
    require(oldCode.run(96000,65535) != 96000, "old 32-bit product fails full brightness counterexample");
    require(repairedCode.run(96000,65535) == 96000, "repaired endpoint equals period");
    require(repairedCode.run(0xffffffffU,65535) == 0xffffffffU, "largest uint32 period endpoint");
    for (uint32_t period : {0U,1U,17777U,65535U,65536U,96000U,120000U,1000000U,0xffffffffU}) {
        uint32_t last = 0;
        for (uint32_t raw = 0; raw <= 65535; ++raw) {
            const uint32_t actual = repairedCode.run(period,raw);
            require(actual == expectedDuty(period,raw), "actual repaired x86 division matches independent oracle");
            require(actual == exactDuty(period,raw), "published helper agrees with emitted instructions");
            require(actual >= last && actual <= period, "bounded monotone brightness");
            last = actual;
            ++arithmeticCases;
        }
    }
    std::vector<uint8_t> image(FunctionOffset + sizeof(NativeBody) + 64);
    std::memcpy(image.data() + FunctionOffset, NativeBody, sizeof(NativeBody));
    uint32_t count = 99;
    require(eligible(image.data(),image.size(),FunctionOffset,count) && count == 1, "one exact pristine body admitted");
    require(!eligible(image.data(),image.size(),FunctionOffset+1,count), "symbol offset mismatch refused");
    require(!eligible(image.data(),FunctionOffset+sizeof(NativeBody)-1,FunctionOffset,count), "short mapped image refused");
    for (size_t n = 0; n < sizeof(NativeBody); ++n) {
        image[FunctionOffset+n] ^= 1;
        require(!eligible(image.data(),image.size(),FunctionOffset,count), "every changed donor body byte refused");
        image[FunctionOffset+n] ^= 1;
    }
    std::memcpy(image.data(),Original,sizeof(Original));
    require(!eligible(image.data(),image.size(),FunctionOffset,count) && count == 2, "duplicate arithmetic signature refused");
    std::memset(image.data(),0,sizeof(Original));
    require(eligible(image.data(),image.size(),FunctionOffset,count) && count == 1, "pristine admission retained after counterexamples");
    std::printf("PASS arithmetic_cases=%llu checks=%llu\n", (unsigned long long)arithmeticCases, (unsigned long long)checks);
    return 0;
}
