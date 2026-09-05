"""출판사 원표에서 거리별 반응 분포를 복원한다. 행을 독립 동물로 세지 않는다."""
import json
import posixpath
import re
import zipfile
import xml.etree.ElementTree as E
from pathlib import Path

import numpy as np

from randi_target_response import BASE, save, sha


def main():
    path = BASE / '41586_2023_6683_MOESM10_ESM.xlsx'
    ns = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    contract = {'question': '공개 원표로 광학적 선택성과 사건별 대조를 얼마나 확인할 수 있는가',
                'source': 'https://www.nature.com/articles/s41586-023-06683-4',
                'file_sha256': sha(path), 'code_sha256': sha(Path(__file__)),
                'endpoint': 'EDFig2ij 각 거리 열의 유한 값 수·중앙값·75백분위·0.1 초과 비율',
                'threshold': '논문 도표에 명시된 dF/F 0.1; 추론 검정 문턱 아님',
                'scope': '이미 본 도표의 원표 기술통계; 표적 autoresponse 조건부, 사건·동물 대응 미확인',
                'claim_ceiling': 'BIO_EVIDENCE_L1 descriptive source data; no per-edge causality'}
    save('randi_optical_source_data_contract.json', contract)
    sheets = {}
    with zipfile.ZipFile(path) as z:
        shared = []
        if 'xl/sharedStrings.xml' in z.namelist():
            shared = [''.join(el.text or '' for el in si.iter('{'+ns['s']+'}t'))
                      for si in E.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si', ns)]
        rels = {x.get('Id'): x.get('Target') for x in E.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
        wb = E.fromstring(z.read('xl/workbook.xml'))
        for sheet in wb.findall('s:sheets/s:sheet', ns):
            rid = sheet.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
            target = rels[rid]
            name = target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/'+target)
            data = {}
            for c in E.fromstring(z.read(name)).findall('.//s:sheetData/s:row/s:c', ns):
                v = c.find('s:v', ns)
                if v is None:
                    continue
                text = v.text
                data[c.get('r')] = shared[int(text)] if c.get('t') == 's' else float(text)
            sheets[sheet.get('name')] = data
    data = sheets['EDFig2ij']
    groups = {}
    for col in ('A', 'B', 'C'):
        vals = np.array([v for key,v in data.items() if re.fullmatch(col+r'[0-9]+', key) and key != col+'1' and isinstance(v, (int,float))])
        assert len(vals) and np.isfinite(vals).all()
        groups[data[col+'1']] = {'n':len(vals), 'median':float(np.median(vals)),
                                'q75':float(np.quantile(vals,.75)),
                                'above_0_1':int(np.sum(vals>.1)), 'fraction_above_0_1':float(np.mean(vals>.1))}
    result = {'source_sha256':sha(path), 'sheets':list(sheets), 'offset_trace_panel_e_present': 'EDFig2e' in sheets,
              'groups':groups, 'event_and_animal_ids_in_distance_sheet':False,
              'limitations':['거리 열은 독립 분포이며 행끼리 대응하지 않음',
                             '서로 다른 거리의 반응은 광학 효과와 신경 전달을 분리하지 못함',
                             '세션 6·9에 연결할 사건 ID가 없어 개별 보정에 사용하지 않음']}
    save('randi_optical_source_data_result.json', result)
    print(json.dumps(result,ensure_ascii=False))


if __name__ == '__main__':
    main()
