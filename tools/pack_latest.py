"""Build the latest partial EFI distribution; never reads a live ESP or identity."""
from pathlib import Path
import argparse, hashlib, json, sys, zipfile

ROOT=Path(__file__).resolve().parents[1]
PROFILE='latest-20261116'
def sha(data): return hashlib.sha256(data).hexdigest()

def build(output):
    from verify_package import verify
    verify(ROOT,PROFILE)
    profile=ROOT/'profiles'/PROFILE
    manifest=json.loads((profile/'efi-manifest.json').read_text(encoding='utf-8'))
    meta=json.loads((profile/'metadata.json').read_text(encoding='utf-8'))
    assert meta['runtimeVerified'] is False and meta['assembledFullEFIIncluded'] is False
    data={}
    for name,record in manifest.items():
        payload=(profile/'EFI'/name).read_bytes()
        assert len(payload)==record['bytes'] and sha(payload)==record['sha256']
        data['EFI/'+name]=payload
    for source,target in (
        ('profiles/'+PROFILE+'/metadata.json','metadata/profile.json'),
        ('profiles/'+PROFILE+'/dependencies.json','metadata/dependencies.json'),
        ('profiles/'+PROFILE+'/efi-manifest.json','metadata/efi-manifest.json'),
        ('profiles/'+PROFILE+'/README.md','docs/PROFILE.md'),
        ('docs/issues/usb-typec-20261116.md','docs/USB-TYPEC.md'),
        ('docs/INSTALL.md','docs/INSTALL.md'),('docs/DEPENDENCIES.md','docs/DEPENDENCIES.md'),
        ('docs/CPU_POLICY.md','docs/CPU_POLICY.md'),('docs/THIRD_PARTY.md','docs/THIRD_PARTY.md'),
        ('LICENSE','LICENSE'),('licenses/OpenCore-BSD-3-Clause.txt','licenses/OpenCore-BSD-3-Clause.txt'),
        ('licenses/WhateverXe-BSD-3-Clause.txt','licenses/WhateverXe-BSD-3-Clause.txt'),
        ('src/WhateverXe/source-manifest.json','source/WEX-source-manifest.json')):
        data[target]=(ROOT/source).read_bytes()
    release={'schema':1,'profile':PROFILE,'completeBootImage':False,'runtimeVerified':False,
             'experimentalUSB':True,'highRefreshEnabled':False,'publicEFIFileCount':len(manifest),
             'sourceRepository':'https://github.com/gndb/Thunderobot-R16-A788-Hackintosh',
             'sourceProfile':'profiles/'+PROFILE,'identityMustBeGeneratedLocally':True}
    data['release.json']=(json.dumps(release,indent=2)+'\n').encode()
    data['README.md']=('''# R16 A788: latest deployed partial EFI, 2026-11-16

This is a sanitized configuration and partial payload distribution, not a complete boot image.
It retains WEX 0.8.2-R16 and the existing graphics/power/brightness configuration; high refresh stays disabled.
UTBMap is 1.0.3 (10 selected ports). AirportRTW 2.3.3 is an external dependency, not bundled.
The latest USB revision has no completed runtime acceptance record. USB-C/PD and display recovery remain unresolved.
The previously observed successful 2026-11-14 profile is retained separately in the repository.

Use metadata/dependencies.json for this profile's exact dependency versions and hashes.
Supply the missing drivers, your own SMBIOS identity, and locally generated CPUFriend data.
System-side Intel and NVIDIA drivers must be installed separately; copying EFI cannot perform that installation.
See docs/INSTALL.md, docs/PROFILE.md, and docs/USB-TYPEC.md. Some documentation links target the repository.

Source, historical profiles, and issue reports:
https://github.com/gndb/Thunderobot-R16-A788-Hackintosh/tree/main/profiles/latest-20261116
''').encode()
    index={n:{'bytes':len(b),'sha256':sha(b)} for n,b in sorted(data.items())}
    data['file-manifest.json']=(json.dumps(index,indent=2)+'\n').encode()
    output.mkdir(parents=True,exist_ok=True)
    target=output/'R16-A788-latest-20261116-partial-EFI.zip'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for name,payload in sorted(data.items()):
            info=zipfile.ZipInfo(name,(2026,11,16,0,0,0))
            info.create_system=3
            info.external_attr=0o100644<<16
            info.compress_type=zipfile.ZIP_DEFLATED
            archive.writestr(info,payload)
    with zipfile.ZipFile(target) as archive:
        assert archive.testzip() is None
        assert len(archive.namelist())==len(set(archive.namelist()))
        assert set(archive.namelist())==set(data)
        for name,record in index.items():
            payload=archive.read(name)
            assert sha(payload)==record['sha256'] and len(payload)==record['bytes']
    checksum=sha(target.read_bytes())
    (output/'SHA256SUMS.txt').write_text(checksum+'  '+target.name+'\n',encoding='ascii')
    print(json.dumps({'profile':PROFILE,'asset':target.name,'sha256':checksum,'bytes':target.stat().st_size,'completeBootImage':False}))
    return target

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    build(args.output)
