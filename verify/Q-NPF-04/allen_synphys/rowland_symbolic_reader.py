"""Protocol-3 피클의 허용 참조를 비실행 기호로 읽고 큰 배열은 파일 구간으로 보존한다."""
from dataclasses import dataclass
from pathlib import Path
import pickle
import struct

import numpy as np


@dataclass(frozen=True)
class ByteRange:
    path: str
    offset: int
    size: int


class Symbol:
    reference = None
    args = ()
    state = None

    def __new__(cls, *args, **kwargs):
        return object.__new__(cls)

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def __setstate__(self, state):
        self.state = state


class Reader(pickle._Unpickler):
    # Python 3.11 내부 dispatch를 사용한다. protocol 4 frame·확장 캐시는 허용하지 않는다.
    dispatch = pickle._Unpickler.dispatch.copy()
    allowed = {('__main__', 'SessionLite'), ('subsets_analysis', 'Subsets'),
               ('numpy', 'dtype'), ('numpy', 'ndarray'),
               ('numpy.core.multiarray', '_reconstruct'), ('numpy.core.multiarray', 'scalar'),
               ('numpy._core.multiarray', '_reconstruct'), ('numpy._core.multiarray', 'scalar')}

    def __init__(self, stream, path):
        super().__init__(stream)
        self.stream = stream
        self.path = str(Path(path).resolve())
        self.limit = Path(path).stat().st_size
        self.classes = {}

    def find_class(self, module, name):
        reference = (module, name)
        if reference not in self.allowed:
            raise pickle.UnpicklingError(f'Unsupported reference: {reference}')
        if reference not in self.classes:
            self.classes[reference] = type('InertSymbol', (Symbol,), {'reference': reference})
        return self.classes[reference]

    def load_proto(self):
        if self.read(1) != b'\x03':
            raise pickle.UnpicklingError('Only protocol 3 is supported')

    def load_binbytes(self):
        header = self.read(4)
        if len(header) != 4:
            raise EOFError('Incomplete byte length')
        size = struct.unpack('<I', header)[0]
        start = self.stream.tell()
        if start + size > self.limit:
            raise EOFError(f'Incomplete payload: need {start + size} bytes, have {self.limit}')
        if size > 4096:
            self.stream.seek(size, 1)
            self.append(ByteRange(self.path, start, size))
        else:
            self.append(self.read(size))

    def forbidden(self):
        raise pickle.UnpicklingError('Extensions, persistent references and frames are not supported')

    dispatch[pickle.PROTO[0]] = load_proto
    dispatch[pickle.BINBYTES[0]] = load_binbytes
    for opcode in (pickle.EXT1, pickle.EXT2, pickle.EXT4, pickle.PERSID, pickle.BINPERSID, pickle.FRAME):
        dispatch[opcode[0]] = forbidden


def read(path):
    with Path(path).open('rb') as stream:
        value = Reader(stream, path).load()
        if stream.read(1):
            raise pickle.UnpicklingError('Trailing data after STOP')
        return value


def array(value):
    if not isinstance(value, Symbol) or value.reference not in {
            ('numpy.core.multiarray', '_reconstruct'), ('numpy._core.multiarray', '_reconstruct')}:
        raise ValueError('Not a symbolic NumPy array')
    version, shape, dtype_symbol, fortran, payload = value.state
    assert version == 1 and isinstance(dtype_symbol, Symbol) and dtype_symbol.reference == ('numpy', 'dtype')
    dtype = np.dtype(dtype_symbol.args[0])
    if dtype_symbol.state:
        dtype = dtype.newbyteorder(dtype_symbol.state[1])
    if dtype.hasobject:
        raise ValueError('Object arrays require separate inspected decoding')
    assert isinstance(shape, tuple) and all(isinstance(n, int) and n >= 0 for n in shape)
    count = 1
    for n in shape:
        count *= n
    size = count * dtype.itemsize
    order = 'F' if fortran else 'C'
    if isinstance(payload, ByteRange):
        assert payload.size == size
        return np.memmap(payload.path, mode='r', dtype=dtype, offset=payload.offset, shape=shape, order=order)
    assert isinstance(payload, bytes) and len(payload) == size
    return np.frombuffer(payload, dtype=dtype).reshape(shape, order=order)
