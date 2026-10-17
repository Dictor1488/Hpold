#!/usr/bin/env python3
"""inq_hpold standalone native panel package."""
from pathlib import Path
import argparse
import subprocess
import zipfile
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parent
VERSION='0.2.0-alpha1'
LIBS=('base_app-1.0-SNAPSHOT.swc','battle.swc','common-1.0-SNAPSHOT.swc','common_i18n_library-1.0-SNAPSHOT.swc','gui_base-1.0-SNAPSHOT.swc','gui_battle-1.0-SNAPSHOT.swc','gui_lobby-1.0-SNAPSHOT.swc','lobby.swc','playerglobal.swc')

def build(python27):
    for name in LIBS:
        if not (ROOT/'as3/libs'/name).is_file():raise RuntimeError('Missing as3/libs/'+name)
    swf=ROOT/'as3/bin/inq_hpold.swf'
    if not swf.is_file() or swf.read_bytes()[:3] not in (b'FWS',b'CWS',b'ZWS'):raise RuntimeError('Compile inq_hpold.swf with Flex first')
    entries={'res/gui/flash/inq_hpold.swf':swf.read_bytes()}
    for src in sorted((ROOT/'python').rglob('*.py')):
        subprocess.check_call([python27,'-m','py_compile',str(src)])
        pyc=src.with_suffix('.pyc')
        try:
            raw=pyc.read_bytes()
            if raw[:4]!=bytes.fromhex('03f30d0a'):raise RuntimeError('Requires Python 2.7 bytecode')
            entries['res/scripts/client/'+src.relative_to(ROOT/'python').with_suffix('.pyc').as_posix()]=raw
        finally:pyc.unlink(missing_ok=True)
    meta=ET.Element('root')
    for key,val in [('id','inq_hpold'),('version',VERSION),('name','inq_hpold'),('description','Native HP panel indicators')]:
        ET.SubElement(meta,key).text=val
    entries['meta.xml']=ET.tostring(meta,encoding='utf-8',xml_declaration=True)
    out=ROOT/'build'/('inq_hpold_'+VERSION+'.wotmod')
    out.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_STORED) as z:
        for name,data in sorted(entries.items()):
            zi=zipfile.ZipInfo(name,(1980,1,1,0,0,0));zi.compress_type=zipfile.ZIP_STORED;z.writestr(zi,data)
    with zipfile.ZipFile(out) as z:assert z.testzip() is None
    print('Built:',out)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--python27',required=True);a=p.parse_args();build(a.python27)
