# vis: Claude Code 가이드

그림 스킬. 스킬은 `.claude/skills/vis/`, 명령은 `scripts/vis.py`. spec 의 `kind:` 로 종류를 고른다.
- arch: `scripts/archdraw/` (만화풍 아키텍처, HTML·SVG·PNG)
- xref·mindmap·graph: `scripts/visdraw/` (인터랙티브 HTML·PNG)

## 명령
- 테스트: `pytest -q` (PNG 테스트는 Chrome/Edge/Chromium이 있을 때만)
- 예시 다시 그리기: `python .claude/skills/vis/scripts/vis.py examples/<이름>.yaml`
- 아이콘 전체 보기: `python .claude/skills/vis/scripts/vis.py --gallery -o icons`
- 플러그인 점검: `claude plugin validate .`

## 규칙
- 렌더러는 표준 라이브러리 + pyyaml + fonttools만 쓴다. 의존성을 늘리지 않는다. HTML 에 CDN 을 넣지 않는다.
- 그림을 바꾸면 PNG를 직접 열어 눈으로 확인하고, 예시 출력(`examples/`)도 다시 만들어 커밋한다.
- HTML 종류를 바꾸면 브라우저에서 한 번 눌러 본다(칸·tag·노드·검색).
- 아이콘·별칭을 바꾸면 `reference.md` 표도 고친다(테스트가 확인한다).
- 코드를 바꾸면 테스트를 추가하고 `pytest -q`가 통과한 뒤 커밋한다.
- 공개 repo 다. 예시에 고객사·개인 자료를 넣지 않는다.
