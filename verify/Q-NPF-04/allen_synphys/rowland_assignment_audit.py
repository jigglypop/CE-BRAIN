"""기존 자료의 배정 설명과 저장 필드를 점검한다. 수치 분석은 재실행하지 않는다."""
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path

from rowland_sessions import read_sessions
from randi_target_response import save

BASE = Path('data/external/cortical_propagation_2023')


class Paragraphs(HTMLParser):
    def __init__(self):
        super().__init__()
        self.active, self.buffer, self.rows = False, [], []

    def handle_starttag(self, tag, attrs):
        if tag == 'p':
            self.active, self.buffer = True, []

    def handle_data(self, data):
        if self.active:
            self.buffer.append(data)

    def handle_endtag(self, tag):
        if tag == 'p' and self.active:
            self.rows.append(''.join(self.buffer))
            self.active = False


def main():
    source = BASE / 'nature_article_fulltext.html'
    parser = Paragraphs()
    parser.feed(source.read_text(encoding='utf-8'))
    anchors = {
        'catch_assignment': 'randomly interleaved',
        'constrained_assignment': 'three trial types selected pseudorandomly',
        'target_identity': 'subset of neurons to be targeted was selected randomly',
        'separate_reward_segment': 'Before active behavior, 10',
        'trial_exclusions': 'As imaging was stopped intermittently',
        'generic_statement': 'and no randomization was used',
    }
    evidence = {}
    for key, anchor in anchors.items():
        matches = [(i, text) for i, text in enumerate(parser.rows) if anchor in text]
        assert len(matches) == 1, (key, len(matches))
        i, text = matches[0]
        evidence[key] = {'paragraph_index': i, 'sha256': hashlib.sha256(text.encode()).hexdigest()}
    sessions, status = read_sessions(BASE / 'sessions_lite_flu_2022-08-11.pkl')
    assert status['pickle_complete'] and len(sessions) == 11
    required = ['tstart_galvo', 'trial_start', 'trial_subsets', 'pre_reward',
                'pre_rew_trials', 'autorewarded', 'unrewarded_hits', 'first_lick']
    rows = []
    for session in sessions:
        assert all(k in session for k in required)
        rows.append({'mouse': session['mouse'], 'run': session['run_number'],
                     'top_level_keys': sorted(session),
                     'raw_run_present': 'run' in session,
                     'frame_clock_present': 'paqio_frames' in session})
    affected = []
    for root, pattern in [(Path(__file__).parent, 'rowland*'), (Path('paper'), 'Q_NPF_04_S1S2*')]:
        for path in sorted(root.rglob(pattern)):
            if path.suffix not in ('.json', '.md', '.py') or 'assignment' in path.name:
                continue
            if re.search('비무작위|non.random', path.read_text(encoding='utf-8'), re.I):
                affected.append({'path': path.as_posix(), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    result = {
        'question': '시행 배정에 관한 기존 단정 정정과 보유 필드 확인',
        'source': 'https://www.nature.com/articles/s41593-023-01413-5',
        'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'paragraph_evidence': evidence, 'sessions': rows,
        'affected_records_keyword_matches': affected,
        'correction': '시행 의사무작위 배정이 구체적으로 보고됨. 일반 통계절의 무작위화 부정과 문언 충돌은 남음.',
        'limits': ['실행 배정 코드와 조건부 배정 확률은 검증하지 않음',
                   '최상위 필드 목록은 전체 원자료의 부재 증명이 아님',
                   '기존 수치 결과를 변경하거나 직접 S1-S2 경로를 확립하지 않음'],
    }
    save('rowland_assignment_audit_result.json', result)
    print(json.dumps({'sessions': len(rows), 'affected_records': len(affected), 'status': 'PASS'}))


if __name__ == '__main__':
    main()
