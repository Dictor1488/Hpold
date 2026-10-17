#!/usr/bin/env python3
"""Safe, non-executing Python 2.7 marshal reader for the PjOrion wrapper.
Usage: python tools/inspect_py27_pyc.py mod_playersPanelHP.pyc
Works with Python 3. No eval, exec, import of target module.
Only a limited subset of Python 2.7 marshal tags is implemented.
"""
import struct
import sys

class Reader:
    def __init__(self, data):
        self.data = data
        self.pos = 0
        self.interned = []

    def take(self, n):
        if n < 0 or self.pos + n > len(self.data):
            raise ValueError("Invalid length/offset: %d %d" % (self.pos, n))
        result = self.data[self.pos:self.pos+n]
        self.pos += n
        return result

    def integer(self):
        return struct.unpack("<i", self.take(4))[0]

    def read(self):
        tag = self.take(1)
        if tag == b'N': return None
        if tag == b'F': return False
        if tag == b'T': return True
        if tag == b'i': return self.integer()
        if tag == b'I': return struct.unpack("<q", self.take(8))[0]
        if tag in (b's', b't'):
            value = self.take(self.integer())
            if tag == b't':
                self.interned.append(value)
            return value
        if tag == b'R':
            return self.interned[self.integer()]
        if tag == b'u':
            return self.take(self.integer()).decode('utf-8', 'replace')
        if tag in (b'(', b'['):
            return tuple(self.read() for _ in range(self.integer()))
        if tag == b')':
            return tuple(self.read() for _ in range(self.take(1)[0]))
        if tag == b'c':
            result = {name: self.integer() for name in (
                'argcount', 'nlocals', 'stacksize', 'flags')}
            for name in ('code', 'consts', 'names', 'varnames',
                         'freevars', 'cellvars', 'filename', 'name'):
                result[name] = self.read()
            result['firstlineno'] = self.integer()
            result['lnotab'] = self.read()
            return result
        raise ValueError("Unsupported marshal tag %r at %d" % (tag, self.pos-1))

def inspect(path):
    with open(path, 'rb') as stream:
        raw = stream.read()
    if raw[:4] != b'\x03\xf3\r\n':
        raise ValueError("Not a standard Python 2.7 .pyc")
    reader = Reader(raw[8:])
    obj = reader.read()
    if reader.pos != len(raw) - 8:
        raise ValueError("Unused marshal bytes: %d" % (len(raw)-8-reader.pos))
    if not isinstance(obj, dict) or 'code' not in obj:
        raise ValueError("Top-level object is not a code object")
    print("File: %s" % path)
    print("PYC bytes: %d" % len(raw))
    print("Code name: %r" % obj['name'])
    print("Filename: %r" % obj['filename'])
    print("Code bytes: %d" % len(obj['code']))
    print("Globals/names: %r" % (obj['names'],))
    print("Constants: %r" % (obj['consts'],))
    print("Marshal parsed: %d/%d" % (reader.pos, len(raw)-8))
    return obj

if __name__ == '__main__':
    inspect(sys.argv[1])
