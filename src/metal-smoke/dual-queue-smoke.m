#import <Foundation/Foundation.h>
#import <Metal/Metal.h>
#import <IOKit/IOKitLib.h>
#include <dispatch/dispatch.h>
#include <stdint.h>
#include <string.h>
static NSDictionary *identity(id<MTLDevice> d) {
    uint32_t vendor=0, device=0; io_string_t path={0};
    io_registry_entry_t node=IOServiceGetMatchingService(kIOMainPortDefault,IORegistryEntryIDMatching(d.registryID));
    if(node) IORegistryEntryGetPath(node,kIOServicePlane,path);
    while(node) {
        CFTypeRef v=IORegistryEntryCreateCFProperty(node,CFSTR("vendor-id"),kCFAllocatorDefault,0);
        CFTypeRef p=IORegistryEntryCreateCFProperty(node,CFSTR("device-id"),kCFAllocatorDefault,0);
        if(v && p && CFGetTypeID(v)==CFDataGetTypeID() && CFGetTypeID(p)==CFDataGetTypeID() && CFDataGetLength(v)>=4 && CFDataGetLength(p)>=4) {
            memcpy(&vendor,CFDataGetBytePtr(v),4); memcpy(&device,CFDataGetBytePtr(p),4);
        }
        if(v)CFRelease(v); if(p)CFRelease(p);
        if(vendor || device) { IOObjectRelease(node); break; }
        io_registry_entry_t parent=0; kern_return_t r=IORegistryEntryGetParentEntry(node,kIOServicePlane,&parent); IOObjectRelease(node); node=(r==KERN_SUCCESS)?parent:0;
    }
    return @{@"name":d.name?:@"",@"registryID":@(d.registryID),@"vendorID":@(vendor),@"deviceID":@(device),@"vendorHex":[NSString stringWithFormat:@"0x%04x",vendor],@"deviceHex":[NSString stringWithFormat:@"0x%04x",device],@"servicePath":[NSString stringWithUTF8String:path]?:@""};
}
static int emit(NSDictionary *v,int result) { NSData *b=[NSJSONSerialization dataWithJSONObject:v options:NSJSONWritingPrettyPrinted error:NULL]; fwrite(b.bytes,1,b.length,stdout);puts("");return result; }
int main(void) { @autoreleasepool {
    NSMutableArray *devices=[NSMutableArray array], *prepared=[NSMutableArray array], *results=[NSMutableArray array];
    id<MTLDevice> intel=nil,nvidia=nil;
    for(id<MTLDevice> d in MTLCopyAllDevices()) {
        NSDictionary *v=identity(d);[devices addObject:v];
        if([v[@"vendorID"] unsignedIntValue]==0x8086 && [v[@"deviceID"] unsignedIntValue]==0xa788 && [v[@"servicePath"] containsString:@"IGPU"])intel=d;
        if([v[@"vendorID"] unsignedIntValue]==0x10de && [v[@"deviceID"] unsignedIntValue]==0x2c19)nvidia=d;
    }
    NSMutableDictionary *out=[@{@"test":@"two-device queues submitted before waiting",@"devices":devices,@"gpuWorkSubmitted":@NO,@"crossGPUResources":@NO,@"hardwareExecutionOverlapMeasured":@NO} mutableCopy];
    if(!intel||!nvidia||intel.registryID==nvidia.registryID){out[@"passed"]=@NO;out[@"error"]=@"Two distinct physical GPUs not matched";return emit(out,2);}
    NSString *code=@"#include <metal_stdlib>\nusing namespace metal;\nkernel void add256(device const uint *a [[buffer(0)]], device const uint *b [[buffer(1)]], device uint *c [[buffer(2)]], uint i [[thread_position_in_grid]]) { if(i<256) c[i]=a[i]+b[i]; }\n";
    NSUInteger index=0;
    for(id<MTLDevice> dev in @[intel,nvidia]) {
        NSMutableDictionary *result=[@{@"selectedDevice":identity(dev),@"elementsChecked":@256,@"tag":@(index*1000),@"passed":@NO} mutableCopy];[results addObject:result];
        MTLCompileOptions *opts=[MTLCompileOptions new];opts.languageVersion=MTLLanguageVersion2_3;NSError *error=nil;
        id<MTLLibrary> lib=[dev newLibraryWithSource:code options:opts error:&error];
        id<MTLFunction> fun=lib?[lib newFunctionWithName:@"add256"]:nil;
        id<MTLComputePipelineState> pipeline=fun?[dev newComputePipelineStateWithFunction:fun error:&error]:nil;
        if(!pipeline){out[@"passed"]=@NO;out[@"results"]=results;out[@"error"]=error.localizedDescription?:@"Pipeline unavailable";return emit(out,2);}
        id<MTLBuffer> a=[dev newBufferWithLength:1024 options:MTLResourceStorageModeShared],b=[dev newBufferWithLength:1024 options:MTLResourceStorageModeShared],c=[dev newBufferWithLength:1024 options:MTLResourceStorageModeShared];
        if(!a||!b||!c){out[@"passed"]=@NO;out[@"error"]=@"Buffer unavailable";return emit(out,2);}
        for(NSUInteger i=0;i<256;i++){((uint32_t*)a.contents)[i]=(uint32_t)(i+index*1000);((uint32_t*)b.contents)[i]=(uint32_t)(3*i+17);((uint32_t*)c.contents)[i]=0xffffffff;}
        id<MTLCommandQueue> queue=[dev newCommandQueue];id<MTLCommandBuffer> cb=[queue commandBuffer];id<MTLComputeCommandEncoder> enc=[cb computeCommandEncoder];
        NSUInteger threads=MIN((NSUInteger)64,pipeline.maxTotalThreadsPerThreadgroup);
        if(!queue||!cb||!enc||!threads){out[@"passed"]=@NO;out[@"error"]=@"Queue/encoder unavailable";return emit(out,2);}
        [enc setComputePipelineState:pipeline];[enc setBuffer:a offset:0 atIndex:0];[enc setBuffer:b offset:0 atIndex:1];[enc setBuffer:c offset:0 atIndex:2];
        [enc dispatchThreadgroups:MTLSizeMake((256+threads-1)/threads,1,1) threadsPerThreadgroup:MTLSizeMake(threads,1,1)];[enc endEncoding];
        [prepared addObject:@{@"device":dev,@"pipeline":pipeline,@"a":a,@"b":b,@"c":c,@"queue":queue,@"cb":cb,@"result":result}];index++;
    }
    dispatch_group_t group=dispatch_group_create();
    for(NSDictionary *entry in prepared) {id<MTLCommandBuffer> cb=entry[@"cb"];dispatch_group_enter(group);[cb addCompletedHandler:^(id<MTLCommandBuffer> ignored){dispatch_group_leave(group);}];}
    for(NSDictionary *entry in prepared) {id<MTLCommandBuffer> cb=entry[@"cb"];[cb commit];}
    out[@"gpuWorkSubmitted"]=@YES;
    long timedout=dispatch_group_wait(group,dispatch_time(DISPATCH_TIME_NOW,15*NSEC_PER_SEC));
    out[@"timedOut"]=@(timedout!=0);BOOL passed=timedout==0;
    for(NSDictionary *entry in prepared) {
        id<MTLCommandBuffer> cb=entry[@"cb"];id<MTLBuffer> c=entry[@"c"];NSMutableDictionary *result=entry[@"result"];
        result[@"commandStatus"]=@(cb.status);if(cb.error)result[@"commandError"]=cb.error.localizedDescription;
        if(timedout==0 && cb.status==MTLCommandBufferStatusCompleted && !cb.error){
            NSUInteger bad=0,tag=[result[@"tag"] unsignedIntegerValue];
            for(NSUInteger i=0;i<256;i++)if(((uint32_t*)c.contents)[i]!=(uint32_t)(4*i+17+tag))bad++;
            result[@"mismatches"]=@(bad);result[@"lastResult"]=@(((uint32_t*)c.contents)[255]);result[@"expectedLastResult"]=@(1037+tag);result[@"passed"]=@(bad==0);passed=passed && bad==0;
        }else passed=NO;
    }
    out[@"results"]=results;out[@"passed"]=@(passed);return emit(out,passed?0:2);
} }
