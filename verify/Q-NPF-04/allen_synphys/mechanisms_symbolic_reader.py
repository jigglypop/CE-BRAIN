"""투사 자료의 확인된 객체 이름만 비실행 기호로 읽는다."""
import pickle
from pathlib import Path
from rowland_symbolic_reader import Reader, Symbol


class MechanismsReader(Reader):
    allowed = Reader.allowed | {
        ('utils.interareal_analysis', 'interarealProcessing'),
        ('utils.interareal_analysis', 'interarealAnalysis'),
    }


def read_complete(path):
    path=Path(path)
    assert path.suffix=='.pkl', 'Complete payload required'
    with path.open('rb') as stream:
        obj=MechanismsReader(stream,path).load()
        assert isinstance(obj,Symbol)
        assert obj.reference==('utils.interareal_analysis','interarealProcessing')
        assert not stream.read(1), 'Trailing data after STOP'
    return obj


if __name__=='__main__':
    import io
    path=Path(__file__)
    reader=MechanismsReader(io.BytesIO(),path)
    cls=reader.find_class('utils.interareal_analysis','interarealAnalysis')
    assert issubclass(cls,Symbol)
    try:
        reader.find_class('os','system')
    except pickle.UnpicklingError:
        pass
    else:
        raise AssertionError('Unexpected executable reference allowed')
    print('Inert class mapping and unknown reference rejection PASS; payload validation pending')
