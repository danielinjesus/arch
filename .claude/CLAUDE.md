# arch: Claude Code 가이드

만화풍 아키텍처 다이어그램 스킬. 스킬은 `.claude/skills/draw/`, 렌더러는 그 아래 `scripts/archdraw/`.

## 명령
- 테스트: `pytest -q` (PNG 테스트는 Chrome/Edge/Chromium이 있을 때만)
- 예시 다시 그리기: `python .claude/skills/draw/scripts/draw.py examples/translator.yaml`
- 아이콘 전체 보기: `python .claude/skills/draw/scripts/draw.py --gallery -o icons`
- 플러그인 점검: `claude plugin validate .`

## 규칙
- 렌더러는 표준 라이브러리 + pyyaml + fonttools만 쓴다. 의존성을 늘리지 않는다.
- 그림을 바꾸면 PNG를 직접 열어 눈으로 확인하고, 예시 출력(`examples/`)도 다시 만들어 커밋한다.
- 아이콘·별칭을 바꾸면 `reference.md` 표도 고친다(테스트가 확인한다).
- 코드를 바꾸면 테스트를 추가하고 `pytest -q`가 통과한 뒤 커밋한다.
