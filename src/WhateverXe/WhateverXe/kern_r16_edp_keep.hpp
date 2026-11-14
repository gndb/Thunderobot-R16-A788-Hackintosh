// A788 strict firmware eDP preservation decision. Pure comparison only.
// The runtime adapter owns admission, serialization, PG references and MMIO.
#ifndef KERN_R16_EDP_KEEP_HPP
#define KERN_R16_EDP_KEEP_HPP
#include <stdint.h>
namespace R16EDPKeep {
enum Reason : uint32_t {
 Binding=1U<<0, Readout=1U<<1, Power=1U<<2, Pipe=1U<<3,
 Transport=1U<<4, Timing=1U<<5, Format=1U<<6, Source=1U<<7
};
struct Wanted {
 uint32_t func {},timing[6] {},source {};
 bool valid {};
};
struct Live {
 uint32_t func {},conf {},timing[6] {},source {},portLanes {};
};
struct Admission {
 // bound includes opt-in, exact A788/donor, physical panel A/pipe A,
 // object/platform/access associations and native caller serialization.
 bool bound {};
 // Every consumed MMIO word was in the mapped BAR and not all-ones.
 bool readable {};
 // Caller held native PG1 and proved stable ADLS pipe-A power.
 bool powerStable {};
 // Caller proved a live, uncompressed, non-MST/FEC, normal SST transport,
 // valid M/N, selected locked PLL and matching DDI A clock route.
 bool sourceSSTProof {};
};
inline uint32_t field(const void *base,uint32_t offset) {
 uint32_t value;
 __builtin_memcpy(&value,static_cast<const uint8_t *>(base)+offset,4);
 return value;
}
// Exact donor CRTCParams is 240 bytes. Caller proves that buffer before use.
inline Wanted wanted(const void *params) {
 Wanted w {};if(!params)return w;
 w.func=field(params,4);
 for(unsigned i=0;i<6;++i)w.timing[i]=field(params,0x10+4*i);
 w.source=field(params,0x28);w.valid=true;return w;
}
inline uint32_t compare(const Admission &a,const Live &l,const Wanted &w) {
 uint32_t reasons=0;
 if(!a.bound)reasons|=Binding;
 if(!a.readable || !w.valid || l.func==UINT32_MAX || l.conf==UINT32_MAX ||
    l.source==UINT32_MAX || l.portLanes==UINT32_MAX ||
    w.func==UINT32_MAX || w.source==UINT32_MAX)reasons|=Readout;
 if(!a.powerStable)reasons|=Power;
 if((l.conf&0xC0000000U)!=0xC0000000U)reasons|=Pipe;
 // Enabled, DDI A (encoded 1), SST mode 2, no port-sync/HDCP.
 // Unknown native bit8 is preserved and deliberately not interpreted.
 if(!a.sourceSSTProof || (l.func&0xFF000000U)!=0x8A000000U ||
    (l.func&((1U<<15)|(1U<<9))))reasons|=Transport;
 for(unsigned i=0;i<6;++i) {
  if(l.timing[i]==UINT32_MAX || w.timing[i]==UINT32_MAX)reasons|=Readout;
  if(l.timing[i]!=w.timing[i])reasons|=Timing;
 }
 const auto lanes=((l.func>>1)&7)+1;
 const auto wantLanes=((w.func>>1)&7)+1;
 if((lanes!=1 && lanes!=2 && lanes!=4) || lanes!=wantLanes ||
    lanes!=l.portLanes || ((l.func>>20)&7)>3 || ((w.func>>20)&7)>3 ||
    ((l.func^w.func)&0x00700000U) ||
    ((l.func^w.func)&0x7F000000U))reasons|=Format;
 if(l.source!=w.source)reasons|=Source;
 return reasons;
}
inline bool keep(const Admission &a,const Live &l,const Wanted &w) {
 return compare(a,l,w)==0;
}
}
#endif
