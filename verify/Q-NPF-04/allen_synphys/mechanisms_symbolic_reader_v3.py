"""프레임 구간 slice를 실행하지 않는 기호로 보존한다."""
from mechanisms_symbolic_reader_v2 import MechanismsReaderV2


class MechanismsReaderV3(MechanismsReaderV2):
    allowed=MechanismsReaderV2.allowed | {('builtins','slice')}
