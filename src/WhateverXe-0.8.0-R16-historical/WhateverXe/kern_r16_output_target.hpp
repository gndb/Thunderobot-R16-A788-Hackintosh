// Diagnostic certificate follows the original short-circuit evaluation.
#ifndef KERN_R16_OUTPUT_TARGET_HPP
#define KERN_R16_OUTPUT_TARGET_HPP
#include <stdint.h>
namespace R16Output {
struct TargetAudit {
 uint64_t checked {},passed {};uint32_t pipe {~0U},mappingBytes {~0U};
 uint32_t nativeCalled {},nativeResult {~0U},framebufferId {~0U},framebufferIdValid {};
 bool test(unsigned bit,bool pass) {checked|=1ULL<<bit;if(pass)passed|=1ULL<<bit;return pass;}
};
inline bool normalMarker(uint32_t reason,uintptr_t caller,uintptr_t entry,uintptr_t success,bool certified) {
 return certified && ((reason==0 && caller==entry) || (reason==1 && caller==success));
}
}
#endif
