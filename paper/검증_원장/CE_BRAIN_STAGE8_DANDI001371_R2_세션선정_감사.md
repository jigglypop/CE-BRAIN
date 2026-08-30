# CE-BRAIN Stage 8 DANDI 001371 R2 세션선정 감사

Status: `UPDATE_TASK_R2_SESSIONS_FOUND`

기준일: 2026-08-31

R1 결과를 본 뒤 같은 S34·S25 세션의 창이나 축을 조정하지 않았다. 미개봉 development subjects S29·S20에서 trial label과 unit region만 읽어 새 세션 자격을 검사했다.

## 적격 세션

| subject/session | trials | delay only | switch | stay | CA1 | PFC |
|---|---:|---:|---:|---:|---:|---:|
| S29-211118 | 298 | 201 | 77 | 20 | 90 | 52 |
| S29-211122 | 176 | 125 | 37 | 14 | 86 | 49 |
| S20-210519 | 136 | 91 | 33 | 12 | 72 | 30 |

S29-211119는 switch 26으로 탈락했다. S20-210509는 switch 37·stay 15였지만 PFC unit이 0이었고, S20-210520은 switch 17이었다. S20-210517은 unit region metadata가 없고 switch 24·stay 7, S20-210518은 switch 11·stay 7이었다.

R2는 개체 독립성을 위해 S29의 두 적격 세션 중 trial 수가 큰 S29-211118 하나와 S20-210519를 고정한다. 같은 S29의 211122는 R2 결과를 본 뒤 구제용으로 열지 않는다.

**[판정]** `UPDATE_TASK_R2_SESSIONS_FOUND`.

calibration S17과 confirmation S33·S28은 계속 봉인한다.
