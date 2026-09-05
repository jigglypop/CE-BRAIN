"""피클 명령을 실행하지 않고 바이트 구간과 참조 이름만 읽는다. 미완료 파일도 지원."""
import argparse
import collections
import json
import pickletools
import struct
from pathlib import Path

OPCODES = {ord(o.code): o for o in pickletools.opcodes}


def scan(path):
    limit = path.stat().st_size
    counts = collections.Counter()
    globals_seen = set()
    history = collections.deque(maxlen=24)
    blobs = []
    stop = 'EOF_WITHOUT_STOP'
    pending = None
    with path.open('rb') as f:
        while f.tell() < limit:
            offset = f.tell()
            code = f.read(1)
            op = OPCODES.get(code[0])
            if op is None:
                raise ValueError(f'Unknown opcode at {offset}')
            counts[op.name] += 1
            try:
                if op.name in ('BINBYTES', 'BINSTRING', 'BINUNICODE', 'BINBYTES8', 'BINUNICODE8', 'BYTEARRAY8'):
                    width = 8 if op.name.endswith('8') else 4
                    header = f.read(width)
                    if len(header) != width:
                        raise EOFError
                    length = int.from_bytes(header, 'little')
                    start = f.tell()
                    if start + length > limit:
                        pending = {'opcode':op.name, 'opcode_offset':offset, 'data_offset':start,
                                   'declared_bytes':length, 'required_file_bytes':start+length,
                                   'context':list(history)}
                        stop = 'INCOMPLETE_PAYLOAD'
                        break
                    if length > 4096:
                        blobs.append({'opcode':op.name,'data_offset':start,'bytes':length,'context':list(history)})
                        f.seek(length,1)
                        value = {'bytes_skipped':length}
                    else:
                        raw = f.read(length)
                        value = raw.decode('utf-8') if 'UNICODE' in op.name else repr(raw[:80])
                elif op.arg is not None:
                    value = op.arg.reader(f)
                    if f.tell() > limit:
                        raise EOFError
                    if isinstance(value, bytes):
                        value = repr(value[:80])
                    elif not isinstance(value, (str,int,float,bool,type(None))):
                        value = str(value)[:160]
                else:
                    value = None
            except (EOFError, ValueError, struct.error):
                pending = {'opcode':op.name,'opcode_offset':offset,'context':list(history)}
                stop = 'INCOMPLETE_ARGUMENT'
                break
            if op.name == 'GLOBAL':
                globals_seen.add(value)
            history.append({'offset':offset,'opcode':op.name,'value':value})
            if op.name == 'STOP':
                stop = 'STOP_FOUND'
                break
        consumed = f.tell()
    return {'path':str(path),'snapshot_bytes':limit,'consumed_bytes':consumed,'status':stop,
            'pending':pending,'globals':sorted(globals_seen),'opcode_counts':dict(counts),
            'large_payloads':blobs,'executes_pickle':False,
            'claim_ceiling':'L0 syntax inspection; neither complete schema nor biological result'}


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('path',type=Path)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    result=scan(args.path)
    with args.out.open('x',encoding='utf-8') as f:
        json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps({k:v for k,v in result.items() if k not in ('opcode_counts','large_payloads')}))
