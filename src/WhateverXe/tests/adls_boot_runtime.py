#!/usr/bin/env python3
"""A rejected ADL-S boot consumer transition must not start the accelerator."""
from pathlib import Path
import subprocess,tempfile
r=Path(__file__).resolve().parents[1];s=(r/'WhateverXe/kern_xe.cpp').read_text()
a=s.index('bool XE::wrapTGLAcceleratorStart(');b=s.index(' if (callbackXE->adlnDetected',a)
entry=s[a:b]+' return true;\n}'
code='''
#include <cassert>
#include <cstdint>
// This check ends at the ADL-S boot resource gate before native startup. R16
// activation is not modeled as ready: opt-in stays false, counters stay zero,
// and the diagnostic boundary records/rejects any unexpected R16 side effects.
unsigned r16RecordCalls=0;
void r16AccelRecord(uint32_t,uint32_t,uint32_t,uint32_t,bool=false){++r16RecordCalls;}
struct IOService {};
struct XE {
 bool r16AccelR6Requested=false;
 uint32_t r16AccelStartCalls=0,r16AccelStartReject=0;
 bool tglGT2Detected=false,tglGT2Ready=false;
 bool display12SmallGTDetected=false,display12SmallGTReady=true;
 bool adlsDisplaySelected=true,adlsDisplayHooksReady=true,adlsBootConsumersFailed=false;
 static bool wrapTGLAcceleratorStart(IOService*,IOService*);
} xe,*callbackXE=&xe;
'''+entry+'''
int main(){
 assert(XE::wrapTGLAcceleratorStart(nullptr,nullptr));
 xe.adlsBootConsumersFailed=true;
 assert(!XE::wrapTGLAcceleratorStart(nullptr,nullptr));
 xe.adlsDisplaySelected=false;
 assert(XE::wrapTGLAcceleratorStart(nullptr,nullptr));
 xe.adlsDisplaySelected=true;xe.adlsBootConsumersFailed=false;xe.adlsDisplayHooksReady=false;
 assert(!XE::wrapTGLAcceleratorStart(nullptr,nullptr));
 assert(!xe.r16AccelR6Requested && !xe.r16AccelStartCalls && !xe.r16AccelStartReject);
 assert(r16RecordCalls==0);
}
'''
with tempfile.TemporaryDirectory(prefix='adls-boot-runtime-') as d:
 d=Path(d);(d/'test.cpp').write_text(code)
 subprocess.run(['clang++','-std=c++17','-fsanitize=address,undefined',str(d/'test.cpp'),'-o',str(d/'test')],check=True)
 subprocess.run([str(d/'test')],check=True)
print('PASS actual accelerator admission: failed ADL-S boot retirement blocks native start; unrelated backend unchanged')
