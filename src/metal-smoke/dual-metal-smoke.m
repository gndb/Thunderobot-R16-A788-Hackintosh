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
static bool complete(id<MTLCommandBuffer> cb,NSMutableDictionary *out) {
    dispatch_semaphore_t done=dispatch_semaphore_create(0);
    [cb addCompletedHandler:^(id<MTLCommandBuffer> ignored){dispatch_semaphore_signal(done);}];
    [cb commit]; long timeout=dispatch_semaphore_wait(done,dispatch_time(DISPATCH_TIME_NOW,15*NSEC_PER_SEC));
    out[@"timedOut"]=@(timeout!=0); out[@"commandStatus"]=@(cb.status);
    if(cb.error)out[@"commandError"]=cb.error.localizedDescription;
    return timeout==0 && cb.status==MTLCommandBufferStatusCompleted && cb.error==nil;
}
int main(int argc,const char **argv) { @autoreleasepool {
    NSString *stage=argc>1?[NSString stringWithUTF8String:argv[1]]:@"--identity";
    NSString *gpu=argc>2?[NSString stringWithUTF8String:argv[2]]:@"intel";
    if(![gpu isEqual:@"intel"] && ![gpu isEqual:@"nvidia"]) return emit(@{@"passed":@NO,@"error":@"Unknown physical GPU selection"},2);
    uint32_t targetVendor=[gpu isEqual:@"nvidia"]?0x10de:0x8086; uint32_t targetDevice=[gpu isEqual:@"nvidia"]?0x2c19:0xa788;
    NSMutableArray *all=[NSMutableArray array]; id<MTLDevice> dev=nil; NSDictionary *selected=nil;
    for(id<MTLDevice> d in MTLCopyAllDevices()) { NSDictionary *v=identity(d); [all addObject:v]; if([v[@"vendorID"] unsignedIntValue]==targetVendor && [v[@"deviceID"] unsignedIntValue]==targetDevice && (![gpu isEqual:@"intel"] || [v[@"servicePath"] containsString:@"IGPU"])) {dev=d;selected=v;} }
    NSMutableDictionary *out=[@{@"stage":stage,@"devices":all,@"matchedRequestedGPU":@(dev!=nil),@"requestedGPU":gpu,@"gpuWorkSubmitted":@NO} mutableCopy];
    if(!dev){out[@"passed"]=@NO;out[@"error"]=@"No MTLDevice belongs to requested physical PCI GPU";return emit(out,2);}
    out[@"selectedDevice"]=selected;
    if([stage isEqual:@"--identity"]){out[@"passed"]=@YES;return emit(out,0);}
    if(![stage isEqual:@"--compile"] && ![stage isEqual:@"--compute"] && ![stage isEqual:@"--render"]){out[@"passed"]=@NO;out[@"error"]=@"Unknown stage";return emit(out,2);}
    id<MTLComputePipelineState> pipeline=nil;
    if(![stage isEqual:@"--render"]) {
        NSString *code=@"#include <metal_stdlib>\nusing namespace metal;\nkernel void add256(device const uint *a [[buffer(0)]], device const uint *b [[buffer(1)]], device uint *c [[buffer(2)]], uint i [[thread_position_in_grid]]) { if(i<256) c[i]=a[i]+b[i]; }\n";
        MTLCompileOptions *options=[MTLCompileOptions new];options.languageVersion=MTLLanguageVersion2_3;NSError *error=nil;
        id<MTLLibrary> library=[dev newLibraryWithSource:code options:options error:&error];
        if(!library){out[@"passed"]=@NO;out[@"error"]=error.localizedDescription?:@"Library compilation failed";return emit(out,2);}
        id<MTLFunction> function=[library newFunctionWithName:@"add256"];
        pipeline=function?[dev newComputePipelineStateWithFunction:function error:&error]:nil;
        if(!pipeline){out[@"passed"]=@NO;out[@"error"]=error.localizedDescription?:@"Pipeline compilation failed";return emit(out,2);}
        out[@"shaderCompiled"]=@YES;out[@"languageVersion"]=@"Metal2.3";
        if([stage isEqual:@"--compile"]){out[@"passed"]=@YES;return emit(out,0);}
    }
    id<MTLCommandQueue> queue=[dev newCommandQueue];id<MTLCommandBuffer> cb=queue?[queue commandBuffer]:nil;
    if(!cb){out[@"passed"]=@NO;out[@"error"]=@"Could not create command queue/buffer";return emit(out,2);}
    if([stage isEqual:@"--compute"]) {
        const NSUInteger n=256, bytes=n*sizeof(uint32_t);
        id<MTLBuffer> a=[dev newBufferWithLength:bytes options:MTLResourceStorageModeShared];id<MTLBuffer> b=[dev newBufferWithLength:bytes options:MTLResourceStorageModeShared];id<MTLBuffer> c=[dev newBufferWithLength:bytes options:MTLResourceStorageModeShared];
        if(!a||!b||!c){out[@"passed"]=@NO;out[@"error"]=@"Buffer allocation failed";return emit(out,2);}
        for(NSUInteger i=0;i<n;i++){((uint32_t*)a.contents)[i]=(uint32_t)i;((uint32_t*)b.contents)[i]=(uint32_t)(2*i);((uint32_t*)c.contents)[i]=0xffffffffu;}
        id<MTLComputeCommandEncoder> enc=[cb computeCommandEncoder];if(!enc){out[@"passed"]=@NO;out[@"error"]=@"Compute encoder unavailable";return emit(out,2);}
        [enc setComputePipelineState:pipeline];[enc setBuffer:a offset:0 atIndex:0];[enc setBuffer:b offset:0 atIndex:1];[enc setBuffer:c offset:0 atIndex:2];
        NSUInteger threads=MIN((NSUInteger)64,pipeline.maxTotalThreadsPerThreadgroup);if(!threads){out[@"passed"]=@NO;out[@"error"]=@"No supported threadgroup size";return emit(out,2);}
        [enc dispatchThreadgroups:MTLSizeMake((n+threads-1)/threads,1,1) threadsPerThreadgroup:MTLSizeMake(threads,1,1)];[enc endEncoding];
        out[@"gpuWorkSubmitted"]=@YES;if(!complete(cb,out)){out[@"passed"]=@NO;return emit(out,2);}
        NSUInteger bad=0;for(NSUInteger i=0;i<n;i++)if(((uint32_t*)c.contents)[i]!=(uint32_t)(3*i))bad++;
        out[@"elementsChecked"]=@(n);out[@"mismatches"]=@(bad);out[@"firstResult"]=@(((uint32_t*)c.contents)[0]);out[@"lastResult"]=@(((uint32_t*)c.contents)[255]);out[@"expectedLastResult"]=@765;out[@"passed"]=@(bad==0);return emit(out,bad?2:0);
    }
    MTLTextureDescriptor *td=[MTLTextureDescriptor texture2DDescriptorWithPixelFormat:MTLPixelFormatRGBA8Unorm width:16 height:16 mipmapped:NO];td.usage=MTLTextureUsageRenderTarget;td.storageMode=MTLStorageModeShared;
    id<MTLTexture> tex=[dev newTextureWithDescriptor:td];if(!tex){out[@"passed"]=@NO;out[@"error"]=@"Texture allocation failed";return emit(out,2);}
    uint8_t blue[16*16*4], initial[16*16*4];
    for(NSUInteger i=0;i<16*16;i++){blue[i*4]=0;blue[i*4+1]=0;blue[i*4+2]=255;blue[i*4+3]=255;}
    [tex replaceRegion:MTLRegionMake2D(0,0,16,16) mipmapLevel:0 withBytes:blue bytesPerRow:16*4];
    memset(initial,0xa5,sizeof(initial));[tex getBytes:initial bytesPerRow:16*4 fromRegion:MTLRegionMake2D(0,0,16,16) mipmapLevel:0];
    bool initialized=memcmp(initial,blue,sizeof(initial))==0;out[@"initialTextureBlueVerified"]=@(initialized);
    if(!initialized){out[@"passed"]=@NO;out[@"error"]=@"Initial blue texture failed readback";return emit(out,2);}
    MTLRenderPassDescriptor *pass=[MTLRenderPassDescriptor renderPassDescriptor];pass.colorAttachments[0].texture=tex;pass.colorAttachments[0].loadAction=MTLLoadActionClear;pass.colorAttachments[0].storeAction=MTLStoreActionStore;pass.colorAttachments[0].clearColor=MTLClearColorMake(1,0,0,1);
    id<MTLRenderCommandEncoder> enc=[cb renderCommandEncoderWithDescriptor:pass];if(!enc){out[@"passed"]=@NO;out[@"error"]=@"Render encoder unavailable";return emit(out,2);}[enc endEncoding];
    out[@"gpuWorkSubmitted"]=@YES;if(!complete(cb,out)){out[@"passed"]=@NO;return emit(out,2);}
    uint8_t data[16*16*4];memset(data,0xa5,sizeof(data));[tex getBytes:data bytesPerRow:16*4 fromRegion:MTLRegionMake2D(0,0,16,16) mipmapLevel:0];NSUInteger bad=0;
    for(NSUInteger i=0;i<16*16;i++)if(data[i*4]!=255||data[i*4+1]!=0||data[i*4+2]!=0||data[i*4+3]!=255)bad++;
    out[@"renderOperation"]=@"16x16 red render-pass clear and texture readback, no geometry shader test";out[@"pixelsChecked"]=@256;out[@"mismatches"]=@(bad);out[@"firstRGBA"]=@[@(data[0]),@(data[1]),@(data[2]),@(data[3])];out[@"passed"]=@(bad==0);return emit(out,bad?2:0);
} }
