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
    NSString *gpu=argc>1?[NSString stringWithUTF8String:argv[1]]:@"";
    uint32_t vendor=[gpu isEqual:@"intel"]?0x8086:0x10de,device=[gpu isEqual:@"intel"]?0xa788:0x2c19;
    if(![gpu isEqual:@"intel"] && ![gpu isEqual:@"nvidia"])return emit(@{@"passed":@NO,@"error":@"Unknown GPU"},2);
    id<MTLDevice> dev=nil;
    for(id<MTLDevice> d in MTLCopyAllDevices()){NSDictionary *i=identity(d);if([i[@"vendorID"] unsignedIntValue]==vendor && [i[@"deviceID"] unsignedIntValue]==device)dev=d;}
    NSMutableDictionary *out=[@{@"test":@"16x16 fullscreen triangle vertex+fragment raster and readback",@"requestedGPU":gpu,@"gpuWorkSubmitted":@NO,@"passed":@NO} mutableCopy];
    if(!dev){out[@"error"]=@"No physical device matched";return emit(out,2);}out[@"selectedDevice"]=identity(dev);
    NSString *code=@"#include <metal_stdlib>\nusing namespace metal;\nstruct V { float4 position [[position]]; };\nvertex V tri(uint i [[vertex_id]]) { const float2 p[3]={float2(-1,-1),float2(3,-1),float2(-1,3)}; V v; v.position=float4(p[i],0,1); return v; }\nfragment float4 red() { return float4(1,0,0,1); }\n";
    MTLCompileOptions *opts=[MTLCompileOptions new];opts.languageVersion=MTLLanguageVersion2_3;NSError *error=nil;
    id<MTLLibrary> lib=[dev newLibraryWithSource:code options:opts error:&error];
    MTLRenderPipelineDescriptor *pd=[MTLRenderPipelineDescriptor new];pd.vertexFunction=[lib newFunctionWithName:@"tri"];pd.fragmentFunction=[lib newFunctionWithName:@"red"];pd.colorAttachments[0].pixelFormat=MTLPixelFormatRGBA8Unorm;
    if(!lib||!pd.vertexFunction||!pd.fragmentFunction){out[@"error"]=error.localizedDescription?:@"Shader compilation failed";return emit(out,2);}
    id<MTLRenderPipelineState> pipeline=[dev newRenderPipelineStateWithDescriptor:pd error:&error];
    if(!pipeline){out[@"error"]=error.localizedDescription?:@"Render pipeline failed";return emit(out,2);}out[@"shaderPipelineCreated"]=@YES;
    MTLTextureDescriptor *td=[MTLTextureDescriptor texture2DDescriptorWithPixelFormat:MTLPixelFormatRGBA8Unorm width:16 height:16 mipmapped:NO];td.usage=MTLTextureUsageRenderTarget;td.storageMode=MTLStorageModeShared;
    id<MTLTexture> tex=[dev newTextureWithDescriptor:td];id<MTLCommandQueue> queue=[dev newCommandQueue];id<MTLCommandBuffer> cb=[queue commandBuffer];
    if(!tex||!cb){out[@"error"]=@"Texture or command buffer unavailable";return emit(out,2);}
    MTLRenderPassDescriptor *pass=[MTLRenderPassDescriptor renderPassDescriptor];pass.colorAttachments[0].texture=tex;pass.colorAttachments[0].loadAction=MTLLoadActionClear;pass.colorAttachments[0].storeAction=MTLStoreActionStore;pass.colorAttachments[0].clearColor=MTLClearColorMake(0,0,1,1);
    id<MTLRenderCommandEncoder> enc=[cb renderCommandEncoderWithDescriptor:pass];if(!enc){out[@"error"]=@"Render encoder unavailable";return emit(out,2);}
    [enc setRenderPipelineState:pipeline];[enc setViewport:(MTLViewport){0,0,16,16,0,1}];[enc drawPrimitives:MTLPrimitiveTypeTriangle vertexStart:0 vertexCount:3];[enc endEncoding];
    out[@"gpuWorkSubmitted"]=@YES;if(!complete(cb,out))return emit(out,2);
    uint8_t bytes[1024];memset(bytes,0xa5,sizeof(bytes));[tex getBytes:bytes bytesPerRow:64 fromRegion:MTLRegionMake2D(0,0,16,16) mipmapLevel:0];
    NSUInteger bad=0;for(NSUInteger i=0;i<256;i++)if(bytes[4*i]!=255||bytes[4*i+1]!=0||bytes[4*i+2]!=0||bytes[4*i+3]!=255)bad++;
    out[@"pixelsChecked"]=@256;out[@"mismatches"]=@(bad);out[@"firstRGBA"]=@[@(bytes[0]),@(bytes[1]),@(bytes[2]),@(bytes[3])];out[@"passed"]=@(bad==0);return emit(out,bad?2:0);
} }
