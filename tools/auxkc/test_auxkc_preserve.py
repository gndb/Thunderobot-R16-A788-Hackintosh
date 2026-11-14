#!/usr/bin/env python3
"""Isolated source tests. No kmutil execution or live cache modification.

SPDX-License-Identifier: MIT
Copyright (c) 2026 gndb
"""
from pathlib import Path
import copy
import json
import plistlib
import tempfile
from types import SimpleNamespace
import auxkc_preserve as m


def bundle(path, ident):
    (path/'Contents').mkdir(parents=True)
    (path/'Contents/Info.plist').write_bytes(plistlib.dumps({'CFBundleIdentifier': ident, 'CFBundleVersion': '1.0'}))
    (path/'Contents/payload').write_bytes(b'unchanged fixture')


def main():
    cases = ['success', 'generator-fails', 'inspect-fails', 'missing-identity',
             'interrupt-before-build', 'interrupt-after-build', 'interrupt-before-publish',
             'extra-bundle-changed-before-build', 'extra-bundle-changed-after-build',
             'relative-path-rejected', 'duplicate-path-rejected', 'manifest-key-mismatch',
             'local-kext-changed-before-build', 'local-kext-changed-after-build',
             'identity-substring-rejected', 'local-bundle-added-during-build', 'existing-candidate-rejected',
             'candidate-space-member-rejected', 'candidate-extra-field-rejected']
    results=[]
    member='org.example.external\t1.0\t/Library/Apple/DeviceSupport.kext\t'
    header='auxiliary kext collection at /example:\n'
    parser_cases={
        'parser-table-header-and-blanks':('Extension Information:\n\n  \n'+member,False),
        'parser-space-member':(member.replace('\t',' '),True),
        'parser-unknown-line':('unrecognized inspection text',True),
        'parser-extra-field':(member+'unexpected',True),
        'parser-duplicate-section':(member+'\n'+header,True),
        'parser-empty-id':(member.replace('org.example.external',''),True),
        'parser-empty-version':(member.replace('\t1.0\t','\t\t'),True),
        'parser-empty-path':('org.example.external\t1.0\t',True),
        'parser-relative-path':(member.replace('/Library/Apple/','relative/'),True),
        'parser-parent-path':(member.replace('/Apple/','/Apple/../'),True),
        'parser-double-slash-path':(member.replace('/Apple/','//Apple/'),True),
        'parser-invalid-id':(member.replace('org.example.external','org example'),True),
        'parser-invalid-version':(member.replace('\t1.0\t','\t1.0 invalid\t'),True),
    }
    for case,(body,reject) in parser_cases.items():
        error=None
        try:rows=m.auxiliary_members(header+body)
        except RuntimeError as exc:error=str(exc)
        assert (error is not None)==reject,(case,error)
        if not reject:assert len(rows)==1
        results.append({'case':case,'passed':True,'commandsModeled':0})
    for case in cases:
        with tempfile.TemporaryDirectory(prefix='auxkc-fixture-') as temporary:
            root=Path(temporary).resolve()
            local=root/'Extensions';extra=root/'External'/'DeviceSupport.kext'
            bundle(local/'Example.kext','org.example.local')
            bundle(extra,'org.example.external')
            boot,system,live=[root/name for name in ('Boot.kc','System.kc','Live.kc')]
            for p in (boot,system,live):p.write_bytes(p.name.encode())
            inspection='auxiliary kext collection at /example:\nExtension Information:\norg.example.external\t1.0\t'+str(extra)+'\t\n'
            plan=m.create_plan(inspection,local,boot,system,live)
            plan['allowMissingKDK']=True
            out=root/'Candidate.kc';logs=root/'logs'
            if case=='extra-bundle-changed-before-build':(extra/'Contents/payload').write_bytes(b'changed')
            if case=='local-kext-changed-before-build':(local/'Example.kext/Contents/payload').write_bytes(b'changed')
            if case=='relative-path-rejected':
                plan['bundlePaths']=['relative.kext'];plan['bundleManifests']={'relative.kext':{}}
            if case=='duplicate-path-rejected':plan['bundlePaths']*=2
            if case=='manifest-key-mismatch':plan['bundleManifests']={}
            if case=='existing-candidate-rejected':out.write_bytes(b'keep candidate')
            calls=[];checks=[0]
            def interrupt():
                checks[0]+=1
                stop={'interrupt-before-build':1,'interrupt-after-build':2,'interrupt-before-publish':3}.get(case)
                if checks[0]==stop:raise RuntimeError('fixture interruption')
            def command(argv):
                calls.append(argv)
                assert argv[0]=='/usr/bin/kmutil'
                if argv[1]=='create':
                    assert '--allow-missing-kdk' in argv
                    assert set(argv[i+1] for i,x in enumerate(argv) if x=='-p')==set(plan['bundlePaths'])
                    if case=='generator-fails':return SimpleNamespace(returncode=1,stdout='create failed',stderr='')
                    Path(argv[argv.index('-A')+1]).write_bytes(b'candidate fixture')
                    if case=='extra-bundle-changed-after-build':(extra/'Contents/payload').write_bytes(b'changed')
                    if case=='local-kext-changed-after-build':(local/'Example.kext/Contents/payload').write_bytes(b'changed')
                    if case=='local-bundle-added-during-build':bundle(local/'Added.kext','org.example.added')
                    return SimpleNamespace(returncode=0,stdout='created',stderr='')
                if case=='inspect-fails':return SimpleNamespace(returncode=1,stdout='',stderr='inspect failed')
                identities=plan['requiredIdentities'][:-1] if case=='missing-identity' else plan['requiredIdentities']
                lines=[]
                for ident,version in identities:
                    if case=='identity-substring-rejected':ident='prefix.'+ident
                    lines.append(ident+'\t'+version+'\t/example.kext\t')
                if case=='candidate-space-member-rejected':lines.append('org.example.other 1.0 /example.kext')
                if case=='candidate-extra-field-rejected':lines.append('org.example.other\t1.0\t/example.kext\tunexpected')
                return SimpleNamespace(returncode=0,stdout='auxiliary kext collection at /candidate:\n'+'\n'.join(lines),stderr='')
            error=None
            try:m.build_candidate(plan,out,logs,runner=command,interrupt=interrupt)
            except RuntimeError as exc:error=str(exc)
            if case=='success':
                assert error is None,error
                assert out.read_bytes()==b'candidate fixture'
                assert len(calls)==2
            else:
                assert error is not None,case
                assert not out.exists() or (case=='existing-candidate-rejected' and out.read_bytes()==b'keep candidate')
            assert live.read_bytes()==b'Live.kc'
            assert not list(root.glob('.auxkc-candidate-*'))
            results.append({'case':case,'passed':True,'commandsModeled':len(calls),'liveCollectionUnchanged':True})
    print(json.dumps({'scope':'isolated files; subprocess runner mocked', 'actualKmutilExecuted':False,
                      'actualSystemOrEFIChanged':False,'passed':len(results),'failed':0,'cases':results},indent=2))


if __name__=='__main__':main()
