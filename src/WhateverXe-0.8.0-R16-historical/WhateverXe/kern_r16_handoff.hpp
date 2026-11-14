// A788 R9 native display-PM recovery policy. No register or private ABI access.
// The production kernel backend and sanitizer tests instantiate this same runner.
#ifndef WEX_R16_HANDOFF_HPP
#define WEX_R16_HANDOFF_HPP
#include <stdint.h>
namespace R16Handoff {
enum class Phase : uint32_t { Dormant, Ready, Low, ClearIdle, High, Done };
enum class Reason : uint32_t {
 None, Success, NotReady, Scope, AlreadyIdle, SleepBeforeOff, SleepAfterOff,
 Allocation, DownRejected, DownTimeout, ScopeChanged, PowerInvalid,
 WakeRejected, WakeTimeout, SleepAfterWake, Shutdown
};
enum class Scope : uint32_t { Missing, Safe, Unsafe };
struct Gate {
 enum : uint32_t { Unknown=1U, NoGraphics=2U, PendingLoss=4U, SleepPending=8U, Terminal=16U };
 volatile uint32_t blocks {Unknown}, lossEpoch {};
 void update(uint32_t set,uint32_t clear) {
  uint32_t old,next;
  do { old=__sync_fetch_and_add(&blocks,0U);next=(old|set)&~clear; }
  while(!__sync_bool_compare_and_swap(&blocks,old,next));
  if((set&~old)&(PendingLoss|SleepPending|Terminal))__sync_add_and_fetch(&lossEpoch,1U);
 }
 void cancelSleep() {
  uint32_t old,next;
  do { old=__sync_fetch_and_add(&blocks,0U);next=old&~SleepPending;
   if(!(old&(Unknown|NoGraphics)))next&=~PendingLoss;
  } while(!__sync_bool_compare_and_swap(&blocks,old,next));
 }
};
struct Sample {
 Scope scope {Scope::Missing};
 uint32_t wrangler {}, framebuffer {};
 bool capKnown {}, awake {}, sleepSinceArm {}, shutdown {};
};
struct Machine {
 Phase phase {Phase::Dormant};
 Reason reason {Reason::None};
 uint64_t armedAt {}, phaseAt {};
 uint32_t downResult {}, wakeResult {}, clearAttempts {};
 bool idleIntent {};
 template<class Ops> void arm(uint64_t now,Ops &ops) {
  if(phase!=Phase::Dormant)return;
  armedAt=phaseAt=now;phase=Phase::Ready;ops.trace(*this);
 }
 template<class Ops> uint32_t finish(Reason why,Ops &ops) {
  reason=why;phase=Phase::Done;ops.trace(*this);ops.finish();return 0;
 }
 template<class Ops> uint32_t step(uint64_t now,const Sample &s,Ops &ops) {
  if(phase==Phase::Dormant || phase==Phase::Done)return 0;
  if(s.shutdown)return finish(Reason::Shutdown,ops);
  if(phase==Phase::Ready) {
   if(s.sleepSinceArm || (s.capKnown && !s.awake))
    return finish(Reason::SleepBeforeOff,ops);
   if(now-armedAt>=30000)return finish(Reason::NotReady,ops);
   if(!s.capKnown || s.scope==Scope::Missing)return 250;
   if(s.scope!=Scope::Safe)return finish(Reason::Scope,ops);
   if(s.wrangler==1 || s.framebuffer==1)return finish(Reason::AlreadyIdle,ops);
   if(s.wrangler!=4 || s.framebuffer!=2)return 250;
   if(!ops.prepare())return finish(Reason::Allocation,ops);
   // Set ownership before the asynchronous request: even a rejected request
   // gets an explicit false cleanup attempt, because partial acceptance is
   // outside this policy's control.
   idleIntent=true;phase=Phase::Low;phaseAt=now;ops.trace(*this);
   downResult=ops.requestIdle();
   if(downResult) { reason=Reason::DownRejected;phase=Phase::ClearIdle;ops.trace(*this); }
   return 250;
  }
  if(phase==Phase::Low) {
   if(s.sleepSinceArm || !s.awake) { reason=Reason::SleepAfterOff;phase=Phase::ClearIdle;ops.trace(*this);if(!s.awake)return 0; }
   else if(s.scope!=Scope::Safe) { reason=Reason::ScopeChanged;phase=Phase::ClearIdle;ops.trace(*this); }
   else if(s.wrangler==0 || s.framebuffer==0) { reason=Reason::PowerInvalid;phase=Phase::ClearIdle;ops.trace(*this); }
   else if(s.wrangler==1 && s.framebuffer==1) {
    // getPowerState commits after children complete. A successful setter or
    // Wrangler alone is insufficient evidence that native FB doze completed.
    phase=Phase::ClearIdle;ops.trace(*this);
   } else if(now-phaseAt>=25000) { reason=Reason::DownTimeout;phase=Phase::ClearIdle;ops.trace(*this); }
   else return 250;
  }
  if(phase==Phase::ClearIdle) {
   // Never tickle a system without committed Graphics capability. Priority
   // capability notification requeues this callback after a real wake/cancel.
   if(!s.awake)return 0;
   ++clearAttempts;wakeResult=ops.clearIdle();ops.trace(*this);
   if(wakeResult) {
    if(clearAttempts<3)return 250;
    return finish(Reason::WakeRejected,ops);
   }
   idleIntent=false;phase=Phase::High;phaseAt=now;ops.trace(*this);return 250;
  }
  if(phase==Phase::High) {
   if(s.sleepSinceArm || !s.awake)return finish(reason==Reason::None?Reason::SleepAfterWake:reason,ops);
   if(s.scope!=Scope::Safe)return finish(Reason::ScopeChanged,ops);
   if(s.wrangler==4 && s.framebuffer==2)
    return finish(reason==Reason::None?Reason::Success:reason,ops);
   if(now-phaseAt>=15000)return finish(Reason::WakeTimeout,ops);
   return 250;
  }
  return 0;
 }
};
}
#endif
