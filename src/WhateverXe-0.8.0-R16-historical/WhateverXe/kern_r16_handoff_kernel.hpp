// R9 A788 opt-in: a single public display-PM handoff recovery, not engine surgery.
// This is included only by kern_xe.cpp. The default-off path allocates nothing.
#ifndef WEX_R16_HANDOFF_KERNEL_HPP
#define WEX_R16_HANDOFF_KERNEL_HPP
#include "kern_r16_handoff.hpp"
#include <Headers/kern_nvram.hpp>
#include <IOKit/IOService.h>
#include <IOKit/IONotifier.h>
#include <IOKit/pwr_mgt/RootDomain.h>
#include <IOKit/pwr_mgt/IOPM.h>
#include <kern/thread_call.h>
#include <kern/clock.h>
#include <mach/mach_time.h>
namespace R16HandoffKernel {
using namespace R16Handoff;
static constexpr const char *NvKey="4D1FDA02-38C7-4A6A-9CC6-4BCCA8B30102:R16HandoffDiag";
struct Backend {
 // Permanent lifetime follows successful Lilu plugin start. kern_stop refuses
 // unload; XE::deinit is unchanged. No callback/arm can race a thread_call_free.
 volatile uint32_t initState {},claim {}; // init:0/1/2ready/3failed; claim:0/1/2ready/3done
 Gate gate;
 thread_call_t call {};
 IONotifier *note {};
 IOService *fb {},*wrangler {};
 IOPCIDevice *pci {};
 OSDictionary *down {},*up {};
 uint32_t armEpoch {},scopeReject {},displayCount {},wranglerCount {};
 uint32_t nvAttempts {},nvResult {},nvEvents {};
 bool offSubmitted {};
 Sample last;
 Machine machine;
 static uint64_t now() {
  uint64_t ns=0;absolutetime_to_nanoseconds(mach_absolute_time(),&ns);return ns/1000000ULL;
 }
 void queue(uint32_t milliseconds) {
  uint64_t deadline=0;clock_interval_to_deadline(milliseconds,kMillisecondScale,&deadline);
  thread_call_enter_delayed(call,deadline); // return value means "was pending"
 }
 static bool ancestor(IORegistryEntry *child,IORegistryEntry *wanted) {
  // Iterators retain their entries even across detach. Carry one explicit
  // parent retain between iterations; a retained child alone does not pin a
  // borrowed getParentEntry result during concurrent hotplug.
  if(!child)return false;child->retain();
  for(unsigned i=0;child && i<32;++i) {
   if(child==wanted) {child->release();return true;}
   auto it=child->getParentIterator(gIOServicePlane);IORegistryEntry *parent=nullptr;
   if(it) {
    parent=OSDynamicCast(IORegistryEntry,it->getNextObject());
    if(parent)parent->retain();
    if(it->getNextObject()) {if(parent)parent->release();parent=nullptr;}
    it->release();
   }
   child->release();child=parent;
  }
  if(child)child->release();return false;
 }
 static OSIterator *matches(const char *name) {
  auto dict=IOService::serviceMatching(name);if(!dict)return nullptr;
  auto it=IOService::getMatchingServices(dict);dict->release();return it;
 }
 bool serverOpen() {
  auto it=fb->getChildIterator(gIOServicePlane);if(!it)return false;
  bool open=false;
  while(auto obj=it->getNextObject()) {
   auto s=OSDynamicCast(IOService,obj);
   if(s && !s->isInactive() && s->metaCast("IOFramebufferUserClient")) {open=true;break;}
  }
  it->release();return open;
 }
 Sample sample() {
  Sample s;const auto blocks=__sync_fetch_and_add(&gate.blocks,0U);
  s.capKnown=!(blocks&Gate::Unknown);s.awake=blocks==0;
  s.sleepSinceArm=__sync_fetch_and_add(&gate.lossEpoch,0U)!=armEpoch;
  s.shutdown=(blocks&Gate::Terminal)!=0;scopeReject=displayCount=wranglerCount=0;
  // Never enumerate drivers or request PM in a sleep/capability callback.
  if(!s.awake)return s;
  if(!fb || !pci || fb->isInactive() || pci->isInactive() ||
     pci->configRead32(kIOPCIConfigVendorID)!=0xA7888086 || !ancestor(fb,pci)) {
   scopeReject|=1;s.scope=Scope::Unsafe;return s;
  }
  auto displays=matches("IODisplay");
  if(!displays) {scopeReject|=2;return s;}
  bool allBound=true;
  while(auto o=displays->getNextObject()) {
   auto display=OSDynamicCast(IOService,o);
   if(!display || display->isInactive())continue;
   ++displayCount;if(!ancestor(display,fb))allBound=false;
  }
  displays->release();
  if(displayCount>1 || !allBound) {scopeReject|=4;s.scope=Scope::Unsafe;return s;}
  if(displayCount!=1) {scopeReject|=8;return s;}
  auto wranglers=matches("IODisplayWrangler");
  if(!wranglers) {scopeReject|=16;return s;}
  IOService *found=nullptr;
  while(auto o=wranglers->getNextObject()) {
   auto service=OSDynamicCast(IOService,o);
   if(!service || service->isInactive())continue;
   ++wranglerCount;
   if(!found) {found=service;found->retain();}
  }
  wranglers->release();
  if(wranglerCount!=1 || (wrangler && found!=wrangler)) {
   if(found)found->release();scopeReject|=32;
   s.scope=wranglerCount?Scope::Unsafe:Scope::Missing;return s;
  }
  if(!wrangler)wrangler=found;else found->release();
  if(machine.phase==Phase::Ready && !serverOpen()) {scopeReject|=64;return s;}
  s.scope=Scope::Safe;s.wrangler=wrangler->getPowerState();s.framebuffer=fb->getPowerState();
  return s;
 }
 bool prepare() {
  // Build BOTH requests before submitting off: cleanup must not need allocation.
  down=OSDictionary::withCapacity(1);up=OSDictionary::withCapacity(1);
  auto hold=OSNumber::withNumber(15000U,32);
  const bool okay=down && up && hold && down->setObject("IORequestIdle",hold) &&
   up->setObject("IORequestIdle",kOSBooleanFalse);
  if(hold)hold->release();return okay;
 }
 uint32_t requestIdle() {
  // Public owner queues/serializes native framebuffer DPMS, outside all native
  // modeset and power callback stacks. No direct setPowerState/private dispatcher.
  // Revalidate scope after diagnostics/allocation, which can yield to hotplug.
  const auto current=sample();
  if(current.scope!=Scope::Safe || current.wrangler!=4 || current.framebuffer!=2 || !serverOpen())
   return static_cast<uint32_t>(kIOReturnNotReady);
  if(__sync_fetch_and_add(&gate.blocks,0U)!=0 ||
     __sync_fetch_and_add(&gate.lossEpoch,0U)!=armEpoch ||
     !wrangler || wrangler->isInactive())return static_cast<uint32_t>(kIOReturnNotReady);
  offSubmitted=true;return static_cast<uint32_t>(wrangler->setProperties(down));
 }
 uint32_t clearIdle() {
  if(!offSubmitted)return 0; // final gate refused before any true request
  if(__sync_fetch_and_add(&gate.blocks,0U)!=0 || !wrangler || wrangler->isInactive())
   return static_cast<uint32_t>(kIOReturnNotReady);
  const auto result=static_cast<uint32_t>(wrangler->setProperties(up));
  if(!result)offSubmitted=false;return result;
 }
 void finish() {
  if(down) {down->release();down=nullptr;}if(up) {up->release();up=nullptr;}
  if(wrangler) {wrangler->release();wrangler=nullptr;}
  if(fb) {fb->release();fb=nullptr;}if(pci) {pci->release();pci=nullptr;}
  __atomic_store_n(&claim,3U,__ATOMIC_RELEASE);
 }
 static uint32_t checksum(const uint32_t (&w)[128]) {
  uint32_t h=2166136261U;const auto b=reinterpret_cast<const uint8_t *>(w);
  for(unsigned i=0;i<512;++i)if(i<60 || i>=64)h=(h^b[i])*16777619U;
  return h;
 }
 void trace(const Machine &m) {
  uint32_t event=0;
  if(m.phase==Phase::Ready)event=1;
  else if(m.phase==Phase::Low)event=2;
  else if(m.phase==Phase::ClearIdle)event=m.clearAttempts?4:(m.reason==Reason::None?3:7);
  else if(m.phase==Phase::High)event=4;
  else if(m.phase==Phase::Done)
   event=m.reason==Reason::Success?5:
    ((m.reason==Reason::NotReady || m.reason==Reason::DownTimeout || m.reason==Reason::WakeTimeout)?6:7);
  uint32_t w[128] {};
  w[0]=0x48363152U;w[1]=9;w[2]=sizeof(w);w[3]=0x20261111U;
  w[4]=nvAttempts;w[5]=nvResult;w[6]=event;w[7]=static_cast<uint32_t>(m.phase);
  w[8]=static_cast<uint32_t>(m.reason);w[9]=m.downResult;w[10]=m.wakeResult;w[11]=m.clearAttempts;
  w[12]=static_cast<uint32_t>(last.scope);w[13]=last.wrangler;w[14]=last.framebuffer;
  w[16]=(last.capKnown?1U:0U)|(last.awake?2U:0U)|(last.sleepSinceArm?4U:0U)|
   (last.shutdown?8U:0U)|(m.idleIntent?16U:0U);
  w[17]=__sync_fetch_and_add(&gate.lossEpoch,0U);w[18]=scopeReject;
  w[19]=displayCount;w[20]=wranglerCount;const auto ms=now();
  w[21]=static_cast<uint32_t>(ms);w[22]=static_cast<uint32_t>(ms>>32);
  w[23]=__atomic_load_n(&initState,__ATOMIC_ACQUIRE);
  w[15]=checksum(w);
  IORegistryEntry::getRegistryRoot()->setProperty("WEXR16HandoffR9",w,sizeof(w));
  SYSLOG("igfx","R16HandoffR9 event=%u phase=%u reason=%u power=%u/%u scope=%x displays=%u down=%x wake=%x",
   event,w[7],w[8],w[13],w[14],scopeReject,displayCount,w[9],w[10]);
  // Worker-only, bounded, <=512B. No native wrapper or PM observer writes NVRAM.
  const auto bit=event?1U<<event:0;
  if(bit && !(nvEvents&bit) && nvAttempts<8 && preemption_enabled() && ml_get_interrupts_enabled()) {
   nvEvents|=bit;++nvAttempts;w[4]=nvAttempts;w[15]=checksum(w);
   NVStorage storage;const bool initialized=storage.init();
   const bool accepted=initialized && storage.write(NvKey,reinterpret_cast<const uint8_t *>(w),sizeof(w),NVStorage::OptRaw);
   storage.deinit();nvResult=!initialized?1U:(accepted?3U:2U);
   uint32_t status[]={9,nvAttempts,nvResult,event};
   IORegistryEntry::getRegistryRoot()->setProperty("WEXR16HandoffNvramStatus",status,sizeof(status));
  }
 }
 void work() {
  if(__atomic_load_n(&claim,__ATOMIC_ACQUIRE)!=2)return;
  if(machine.phase==Phase::Dormant) {last=sample();machine.arm(now(),*this);}
  last=sample();const auto delay=machine.step(now(),last,*this);
  if(delay && __atomic_load_n(&claim,__ATOMIC_ACQUIRE)==2)queue(delay);
 }
 static void worker(thread_call_param_t self,thread_call_param_t) {static_cast<Backend *>(self)->work();}
 static IOReturn interest(void *target,void *,UInt32 type,IOService *,void *argument,vm_size_t size) {
  auto self=static_cast<Backend *>(target);auto &g=self->gate;
  switch(type) {
  case kIOMessageCanSystemSleep:case kIOMessageSystemWillSleep:case kIOMessageSystemWillPowerOn:
   g.update(Gate::SleepPending,0);break;
  case kIOMessageSystemWillNotSleep:g.cancelSleep();break;
  case kIOMessageSystemHasPoweredOn:g.update(0,Gate::SleepPending);break;
  case kIOMessageSystemWillPowerOff:case kIOMessageSystemWillRestart:g.update(Gate::Terminal,0);break;
  case kIOMessageSystemCapabilityChange: {
   if(!argument || size<sizeof(IOPMSystemCapabilityChangeParameters)) {g.update(Gate::Unknown,0);break;}
   const auto p=static_cast<const IOPMSystemCapabilityChangeParameters *>(argument);
   const bool graphics=(p->toCapabilities&kIOPMSystemCapabilityGraphics)!=0;
   if(p->changeFlags&kIOPMSystemCapabilityWillChange) {if(!graphics)g.update(Gate::PendingLoss,0);}
   else if((p->changeFlags&kIOPMSystemCapabilityDidChange) || p->changeFlags==0)
    g.update(graphics?0U:Gate::NoGraphics,Gate::Unknown|Gate::PendingLoss|(graphics?Gate::NoGraphics:0U));
   break;
  }
  default:break;
  }
  // PM initializes returnValue/maxWaitForReply to zero; synchronous success
  // acknowledges kernel notifications. messageArgument is NOT a userspace cookie.
  if(__atomic_load_n(&self->claim,__ATOMIC_ACQUIRE)==2 &&
     __sync_fetch_and_add(&g.blocks,0U)==0)self->queue(1);
  return kIOReturnSuccess;
 }
 void initialise(bool requested) {
  if(!requested || !__sync_bool_compare_and_swap(&initState,0U,1U))return;
  if(!IOService::getPMRootDomain()) {__atomic_store_n(&initState,3U,__ATOMIC_RELEASE);return;}
  call=thread_call_allocate_with_options(worker,this,THREAD_CALL_PRIORITY_KERNEL,THREAD_CALL_OPTIONS_ONCE);
  if(call)note=registerPrioritySleepWakeInterest(interest,this,nullptr);
  if(!call || !note) {
   // No arm can occur until initState==2. No notifier exists on this failure.
   if(call) {thread_call_free(call);call=nullptr;}
   __atomic_store_n(&initState,3U,__ATOMIC_RELEASE);return;
  }
  __atomic_store_n(&initState,2U,__ATOMIC_RELEASE);
 }
 void arm(IOService *framebuffer,IOPCIDevice *physical) {
  // Called only after native result0 plus the unchanged R7 strict panel target
  // and FBid0 proof. Native stack does no allocation/registry mutations/PM/NVRAM work.
  if(__atomic_load_n(&initState,__ATOMIC_ACQUIRE)!=2 || !framebuffer || !physical ||
     physical->configRead32(kIOPCIConfigVendorID)!=0xA7888086 ||
     !__sync_bool_compare_and_swap(&claim,0U,1U))return;
  framebuffer->retain();physical->retain();fb=framebuffer;pci=physical;
  armEpoch=__sync_fetch_and_add(&gate.lossEpoch,0U);
  __atomic_store_n(&claim,2U,__ATOMIC_RELEASE);queue(1000);
 }
};
static Backend backend;
}
#endif
