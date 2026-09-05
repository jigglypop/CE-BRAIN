"""완전히 도착한 SessionLite 객체만 모은다. 피클 내부 함수를 실행하지 않는다."""
import json
import pickle
from pathlib import Path

from rowland_first_session import BASE
from rowland_symbolic_reader import Reader, Symbol


class ExactReads:
    """잘린 opcode 인수도 EOF로 알린다. 열 때의 파일 길이를 넘겨 읽지 않는다."""
    def __init__(self, stream, limit):
        self.stream, self.limit = stream, limit

    def read(self, size):
        if size < 0 or self.tell() + size > self.limit:
            raise EOFError('Incomplete opcode or payload at snapshot boundary')
        value = self.stream.read(size)
        if len(value) != size:
            raise EOFError('Short read')
        return value

    def readline(self):
        value = self.stream.readline(max(0, self.limit - self.tell()))
        if not value.endswith(b'\n'):
            raise EOFError('Incomplete pickle line')
        return value

    def tell(self):
        return self.stream.tell()

    def seek(self, offset, whence=0):
        return self.stream.seek(offset, whence)


class SessionsReader(Reader):
    dispatch = Reader.dispatch.copy()

    def __init__(self, stream, path):
        super().__init__(ExactReads(stream, Path(path).stat().st_size), path)
        self.limit = self.stream.limit
        self.sessions = []
        self.ends = []

    def build(self):
        pickle._Unpickler.load_build(self)
        obj = self.stack[-1]
        if isinstance(obj, Symbol) and obj.reference == ('__main__', 'SessionLite'):
            assert isinstance(obj.state, dict)
            identity = (obj.state['mouse'], obj.state['run_number'])
            assert identity not in [(s['mouse'], s['run_number']) for s in self.sessions]
            self.sessions.append(obj.state)
            self.ends.append(self.stream.tell())

    dispatch[pickle.BUILD[0]] = build


def read_sessions(path):
    path = Path(path)
    with path.open('rb') as stream:
        reader = SessionsReader(stream, path)
        try:
            reader.load()
        except EOFError as error:
            status = {'pickle_complete': False, 'pending': str(error)}
        else:
            if stream.read(1):
                raise pickle.UnpicklingError('Trailing bytes after STOP')
            status = {'pickle_complete': True, 'pending': None}
    status.update(bytes_at_open=reader.limit, sessions=[
        {'mouse': s['mouse'], 'run_number': s['run_number'], 'object_end': end}
        for s, end in zip(reader.sessions, reader.ends)])
    return reader.sessions, status


def main():
    path = BASE / 'sessions_lite_flu_2022-08-11.pkl'
    if not path.exists():
        path = path.with_suffix('.pkl.partial')
    _, status = read_sessions(path)
    print(json.dumps(status))


if __name__ == '__main__':
    main()
