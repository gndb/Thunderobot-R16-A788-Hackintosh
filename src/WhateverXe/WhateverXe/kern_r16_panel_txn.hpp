// R16/A788 opt-in power preflight. No saved scanout/clock image is replayed.
// The adapter proves object identity and holds PG1/caller serialization.
#ifndef KERN_R16_PANEL_TXN_HPP
#define KERN_R16_PANEL_TXN_HPP
#include <stdint.h>
namespace R16PanelTxn {
constexpr uint32_t Enable=1U<<31,State=1U<<30;
enum : uint32_t {Binding=10,Unreadable=11,Power=12,PanelError=14,
 PanelTimeout=15,AuxTimeout=16,Ready=20,Changed=21,ClockGuard=30,
 Reference=31,DCReadback=32,PLLLock=33,DBUF1Timeout=34,DBUF2Timeout=35,
 OtherPipe=36,EngineGuard=40,EngineAlreadyObserved=41,EngineActivePipe=42,
 EngineAlreadyOn=43,EngineClockInput=44,EngineRepeated=45,EngineCalled=46,EngineTransition=47};
struct Trace {
 uint32_t stage {},actions {},panelResult {~0U},panelPolls {},auxPolls {},
 dbuf1Polls {},dbuf2Polls {},clockCalls {},engineStage {},engineCalls {};
};
// These are ordinary status/config words, not command FIFO/clear-on-read words.
// Word order is the exported record's before/after register map.
constexpr uint32_t regs[] {0x45404,0x46070,0x46000,0x45504,0x45008,0x44FE8,
 0xC7200,0xC7204,0x45444,0x64010,0x70008,0x71008,0x72008,
 0x51004,0x162100,0x162104,0x16210C,0x70180,0x71180,0x72180};
constexpr unsigned RegisterCount=sizeof(regs)/sizeof(regs[0]);
template<class Read> inline void snapshot(Read read,uint32_t *out) {
 for(unsigned i=0;i<RegisterCount;++i)out[i]=read(regs[i]);
}
inline bool nativeFrequency(uint64_t value) {
 return value==614400000ULL || value==624000000ULL || value==1104000000ULL ||
  value==1113600000ULL || value==1296000000ULL || value==1305600000ULL;
}
// Full-init entry is proven by the exact donor's *state* bit tests. Merely
// missing PLL_ENABLE with LOCK still set is insufficient: the other branch
// can call overridePowerWellsState(false), which itself disables the engine.
inline uint32_t engineEligibility(const uint32_t *r,bool ready,uint32_t observed,
                                 uint32_t table,uint64_t frequency) {
 if(!ready)return EngineGuard;
 if(observed)return EngineAlreadyObserved;
 static const unsigned required[]={0,1,2,3,4,5,6,7,8,9,10,11,12,13,17,18,19};
 for(auto i:required)if(r[i]==~0U)return Unreadable;
 if(!(r[0]&1))return Power;
 if(((r[10]|r[11]|r[12])&(Enable|State)) || ((r[17]|r[18]|r[19])&Enable))return EngineActivePipe;
 if((r[1]&State) && (r[4]&State))return EngineAlreadyOn;
 // A request-on/state-off transition can finish before native entry and
 // select its unsafe already-on branch. Require at least one stable-off
 // PLL/DBUF input, with both request and state clear, to force full-init.
 if((r[1]&(Enable|State)) && (r[4]&(Enable|State)))return EngineTransition;
 if(table>2 || table!=(r[13]>>29) || !nativeFrequency(frequency))return EngineClockInput;
 return EngineCalled;
}
template<class Read,class Write,class Clock,class Panel,class Delay>
inline void prepare(Read read,Write write,Clock clock,Panel panel,Delay delay,
                    bool clockReady,uint32_t table,Trace &t) {
 uint32_t r[RegisterCount];snapshot(read,r);
 // All required inputs must be readable before a single optional write.
 // PHY words are read-only diagnostics and may be inaccessible while off.
 for(unsigned i=0;i<14;++i)if(r[i]==~0U){t.stage=Unreadable;return;}
 if(!(r[0]&1)){t.stage=Power;return;}
 if((r[11]|r[12])&(Enable|State)){t.stage=OtherPipe;return;}
 const bool pllOff=!(r[1]&Enable);
 if(pllOff && !clockReady){t.stage=ClockGuard;return;}
 const auto ref=r[13]>>29;
 if(pllOff && (ref>2 || table>2 || table!=ref)){t.stage=Reference;return;}
 if(!pllOff && !(r[1]&State)){t.stage=PLLLock;return;}
 const bool recover=pllOff || (r[4]&(Enable|State))!=(Enable|State) || (r[5]&(Enable|State))!=(Enable|State);
 if(recover && (r[3]&3)) {
  t.actions|=2;write(0x45504,r[3]&~3U);delay(100);
  const auto dc=read(0x45504);
  if(dc==~0U){t.stage=Unreadable;return;}
  if(dc&3){t.stage=DCReadback;return;}
 }
 if(pllOff) {
  static const uint64_t vco[]={1305600000ULL,1296000000ULL,1305600000ULL};
  t.actions|=4;++t.clockCalls;clock(vco[ref]);
  const auto pll=read(0x46070);
  if(pll==~0U){t.stage=Unreadable;return;}
  if((pll&(Enable|State))!=(Enable|State)){t.stage=PLLLock;return;}
 }
 // Native setter already polls lock (200 x 1ms). Request both existing
 // DBUF slices only after lock is proven, including PLL-on/DBUF-off wake.
 for(unsigned i=0;i<2;++i) {
  const auto reg=i ? 0x44FE8U : 0x45008U;
  auto value=read(reg);
  if(value==~0U){t.stage=Unreadable;return;}
  if((value&(Enable|State))!=(Enable|State)) {
   t.actions|=8U<<i;write(reg,value|Enable);
   value=read(reg);auto &polls=i ? t.dbuf2Polls : t.dbuf1Polls;
   while(value!=~0U && (value&(Enable|State))!=(Enable|State) && polls<100) {
    delay(10);++polls;value=read(reg);
   }
   if(value==~0U){t.stage=Unreadable;return;}
   if((value&(Enable|State))!=(Enable|State)){t.stage=i ? DBUF2Timeout : DBUF1Timeout;return;}
  }
 }
 auto pp=read(0xC7200);
 if(pp==~0U){t.stage=Unreadable;return;}
 if(!(pp&Enable)) {
  t.actions|=32;t.panelResult=panel();
  pp=read(0xC7200);
  if(pp==~0U){t.stage=Unreadable;return;}
  if(t.panelResult){t.stage=PanelError;return;}
  while(!(pp&Enable) && t.panelPolls<500) {
   delay(100);++t.panelPolls;pp=read(0xC7200);
   if(pp==~0U){t.stage=Unreadable;return;}
  }
  if(!(pp&Enable)){t.stage=PanelTimeout;return;}
 }
 auto aux=read(0x45444);
 if(aux==~0U){t.stage=Unreadable;return;}
 if(!(aux&1)) {
  t.actions|=64;write(0x45444,aux|2U);aux=read(0x45444);
  while(aux!=~0U && !(aux&1) && t.auxPolls<100) {
   delay(10);++t.auxPolls;aux=read(0x45444);
  }
  if(aux==~0U){t.stage=Unreadable;return;}
  if(!(aux&1)){t.stage=AuxTimeout;return;}
 }
 t.stage=(t.actions&~1U) ? Changed : Ready;
}
}
#endif
