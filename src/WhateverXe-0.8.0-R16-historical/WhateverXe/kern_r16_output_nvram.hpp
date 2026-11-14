// R7 bounded output checkpoint helper. Integration is owned by XE.
// The caller must already prove the R16/A788 diagnostic opt-in and must not
// call while holding a spin lock, with interrupts disabled, or during panic.
#ifndef R16_OUTPUT_NVRAM_DRAFT_HPP
#define R16_OUTPUT_NVRAM_DRAFT_HPP
#ifdef R16_OUTPUT_NVRAM_HOST_TEST
#include <cstdint>
#include <cstring>
#else
#include <Headers/kern_nvram.hpp>
#include <kern/sched_prim.h>
#include <kern/clock.h>
#include <mach/mach_time.h>
#include <i386/machine_routines.h>
#endif

namespace R16OutputNvram {
constexpr char Key[] = "4D1FDA02-38C7-4A6A-9CC6-4BCCA8B30102:R16OutputDiag";
constexpr uint32_t RecordWords = 56, BlobWords = 128, MaxAttempts = 8;
enum Result : uint32_t {
    Never = 0, InitFailed = 1, WriteRejected = 2, Accepted = 3,
    UnsafeContext = 4, Busy = 5, Budget = 6, DuplicatePhase = 7, InvalidPhase = 8
};
// Permanent zero-initialized member of the existing adapter, not stack-local
// per call. The eight phases are one-shot checkpoints chosen by the caller.
struct State {
    volatile uint32_t busy {}, unsafeSkips {}, busySkips {};
    uint32_t attempts {}, phases {}, previousResult {};
    volatile uint32_t firstClaimed {}; // 0 empty, 1 copying, 2 committed
    uint32_t firstFailure[RecordWords] {};
};
struct Blob { uint32_t words[BlobWords] {}; };
static_assert(sizeof(Blob) == 512, "single diagnostic variable size cap");

inline uint32_t checksum(const Blob &blob) {
    uint32_t value = 2166136261U;
    const auto *bytes = reinterpret_cast<const uint8_t *>(&blob);
    for (uint32_t i = 0; i < sizeof(blob); ++i) {
        if (i >= 60 && i < 64) continue; // word 15 stores this checksum
        value = (value ^ bytes[i]) * 16777619U;
    }
    return value; // integrity check only, not authentication
}

// Only a proved native failure or installation failure may set nativeFailure.
// A target-policy decline is informational and must pass false.
// Fixed-size memory-only first-failure capture: safe before the I/O context
// guard. There is no allocation, pointer serialization, spinning or retry.
inline bool rememberFirstFailure(State &s, const uint32_t (&record)[RecordWords]) {
    if (!__sync_bool_compare_and_swap(&s.firstClaimed, 0U, 1U)) return false;
    memcpy(s.firstFailure, record, sizeof(s.firstFailure));
    __atomic_store_n(&s.firstClaimed, 2U, __ATOMIC_RELEASE);
    return true;
}

enum Phase : uint32_t {
    SetMode3Entry=1, SetMode3Exit=2, SetMode4Entry=3, SetMode4Exit=4,
    LightUpEntry=5, LightUpExit=6, Install=7, FirstNativeFailure=8
};

template<class Storage, class Environment>
inline Result checkpointWith(State &s, const uint32_t (&latest)[RecordWords],
                             bool nativeFailure, uint32_t phase, uint32_t buildId,
                             Storage &storage, Environment &environment) {
    if (phase < 1 || phase > 8) return InvalidPhase;
    if (nativeFailure) rememberFirstFailure(s, latest);
    // These routines are kernel exports, not raw EFI runtime entry points.
    // Both checks precede allocation, IORegistry access, and SYSLOG.
    if (!environment.safe()) {
        __sync_add_and_fetch(&s.unsafeSkips, 1U);
        return UnsafeContext;
    }
    // No spinning, sleeping private mutex, or lock held across Apple NVRAM.
    if (!__sync_bool_compare_and_swap(&s.busy, 0U, 1U)) {
        __sync_add_and_fetch(&s.busySkips, 1U);
        return Busy;
    }
    const uint32_t phaseBit = 1U << (phase - 1);
    if (s.phases & phaseBit) { __sync_lock_release(&s.busy); return DuplicatePhase; }
    if (s.attempts >= MaxAttempts) { __sync_lock_release(&s.busy); return Budget; }
    s.phases |= phaseBit;
    ++s.attempts; // Count attempts, including init/write failure. Never retry.
    const bool firstValid = __atomic_load_n(&s.firstClaimed, __ATOMIC_ACQUIRE) == 2U;

    Blob blob;
    auto *w = blob.words;
    w[0] = 0x4F363152U; // little-endian bytes "R16O"
    w[1] = 7; w[2] = sizeof(blob); w[3] = buildId;
    w[4] = phase; w[5] = s.attempts; w[6] = s.previousResult;
    w[7] = firstValid;
    uint64_t utcSeconds = 0, uptimeTicks = 0;
    environment.clock(utcSeconds, uptimeTicks);
    w[8] = static_cast<uint32_t>(utcSeconds); w[9] = static_cast<uint32_t>(utcSeconds >> 32);
    w[10] = static_cast<uint32_t>(uptimeTicks); w[11] = static_cast<uint32_t>(uptimeTicks >> 32);
    w[12] = RecordWords; w[13] = firstValid ? RecordWords : 0; w[14] = s.phases;
    memcpy(w + 16, latest, sizeof(latest));
    if (firstValid) memcpy(w + 72, s.firstFailure, sizeof(s.firstFailure));
    w[15] = checksum(blob);

    const bool initialized = storage.init();
    const bool accepted = initialized && storage.write(
        Key, reinterpret_cast<const uint8_t *>(&blob), sizeof(blob), Storage::OptRaw);
    storage.deinit(); // required even if init failed
    const Result result = !initialized ? InitFailed : (accepted ? Accepted : WriteRejected);
    s.previousResult = result;
    uint32_t status[] {7, s.attempts, result, phase,
        __sync_fetch_and_add(&s.unsafeSkips, 0U), __sync_fetch_and_add(&s.busySkips, 0U), s.phases, 0};
    // Only the in-memory status knows THIS call's result. A later NVRAM blob
    // can report it as previousResult. Accepted never claims firmware flush.
    environment.publish(status);
    __sync_lock_release(&s.busy);
    return result;
}

#ifndef R16_OUTPUT_NVRAM_HOST_TEST
struct KernelEnvironment {
    bool safe() const { return preemption_enabled() && ml_get_interrupts_enabled(); }
    void clock(uint64_t &utcSeconds, uint64_t &uptimeTicks) const {
        clock_sec_t seconds = 0; clock_usec_t microseconds = 0;
        clock_get_calendar_microtime(&seconds, &microseconds);
        utcSeconds = seconds; uptimeTicks = mach_absolute_time();
    }
    void publish(uint32_t (&status)[8]) const {
        IORegistryEntry::getRegistryRoot()->setProperty("WEXR16OutputNvramStatus", status, sizeof(status));
        IORegistryEntry::getRegistryRoot()->setProperty("WEXR16OutputNvramLastWriteAck", status[2], 32);
        SYSLOG("igfx", "R16OutputDiag phase=%u attempt=%u status=%u bytes=%u", status[3], status[1], status[2], 512U);
    }
};
inline Result checkpoint(State &s, const uint32_t (&latest)[RecordWords],
                         bool nativeFailure, uint32_t phase, uint32_t buildId) {
    NVStorage storage;
    KernelEnvironment environment;
    return checkpointWith(s, latest, nativeFailure, phase, buildId, storage, environment);
}
#endif
} // namespace R16OutputNvram
#endif
