"""프레임 범위도 실행하지 않는 기호로 보존하는 후속 판독기."""
from mechanisms_symbolic_reader import MechanismsReader


class MechanismsReaderV2(MechanismsReader):
    allowed = MechanismsReader.allowed | {('builtins', 'range')}
