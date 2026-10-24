# 데이터 파이프라인 한 장 지도 빌더 - 아이콘을 data URI 로 넣어 HTML 한 파일을 만든다
import base64, html, pathlib, sys

ICON_ROOT = pathlib.Path(r"C:\Users\aidan\OneDrive - Daun Lee\커리어\GCP\Google Architecture")
LEG = ICON_ROOT / "google-cloud-legacy-icons"
CORE = ICON_ROOT / "core-products-icons" / "Unique Icons"
CAT = ICON_ROOT / "category-icons" / "Category Icons"


def leg(n):
    return LEG / n / f"{n}.svg"


def core(folder, file):
    return CORE / folder / "SVG" / file


def cat(folder, file):
    return CAT / folder / "SVG" / file


def uri(p):
    return "data:image/svg+xml;base64," + base64.b64encode(pathlib.Path(p).read_bytes()).decode()


D = "https://docs.cloud.google.com/"

# 단계: (번호, 동사, 영어, 부제, 카드 목록)
# 카드: name, sub(약어·옛 이름), icon, what, why, dest, url
STAGES = [
    ("흩어진 데이터", "Sources", "회사 안팎 여기저기", [
        dict(name="운영 DB", sub="온프레미스 · AWS · Cloud SQL", icon=cat("Databases", "Databases-512-color.svg"),
             what="주문·회원처럼 앱이 매일 읽고 쓰는 DB", why="회사 데이터의 가장 큰 원천이에요"),
        dict(name="파일", sub="CSV · Parquet · S3 · Blob", icon=cat("Storage", "Storage-512-color.svg"),
             what="쌓여 있는 로그·내보내기 파일", why="시스템끼리 가장 흔히 주고받는 형태예요"),
        dict(name="실시간 이벤트", sub="클릭 · 앱 로그 · IoT", icon=cat("Web & Mobile", "WebMobile-512-color.svg"),
             what="끊임없이 흘러오는 작은 메시지", why="지금 무슨 일이 일어나는지 알려줘요"),
        dict(name="SaaS", sub="GA4 · Salesforce 등", icon=cat("Integration Services", "IntegrationServices-512-color.svg"),
             what="광고·CRM 같은 외부 서비스 데이터", why="회사 밖에 있지만 분석엔 꼭 필요해요"),
    ]),
    ("모으기", "Ingest", "한곳으로 들여오기", [
        dict(name="Datastream", sub="CDC", icon=leg("datastream"), dest="→ BigQuery · GCS",
             what="DB 에서 바뀐 것만 실시간 복제", why="운영 DB 를 건드리지 않고 변경분을 바로 가져와요",
             url=D + "datastream/docs/overview"),
        dict(name="BigQuery Data Transfer Service", sub="DTS", icon=leg("data_transfer"), dest="→ BigQuery 전용",
             what="정해진 주기로 가져오는 정기 배송", why="코드 없이 파일·SaaS·DB 를 일정대로 들여와요",
             url=D + "bigquery/docs/dts-introduction"),
        dict(name="Pub/Sub", sub="+ Managed Kafka", icon=leg("pubsub"), dest="→ Dataflow · BigQuery",
             what="이벤트를 받아 나눠 주는 우체국", why="보내는 쪽과 받는 쪽을 떼어 놓고 실시간으로 받아요",
             url=D + "pubsub/docs/overview"),
        dict(name="Storage Transfer Service", sub="STS", icon=leg("transfer"), dest="→ Cloud Storage",
             what="파일을 대량으로 옮기는 이삿짐 센터", why="S3·Azure·사내 파일을 레이크로 옮겨요",
             url=D + "storage-transfer/docs/overview"),
    ]),
    ("다듬기", "Process", "넣기 전에 가공 (ETL)", [
        dict(name="Dataflow", sub="Apache Beam", icon=leg("dataflow"), dest="→ 어디로든",
             what="batch·streaming 을 같은 코드로 가공하는 공장", why="실시간 처리, 넣기 전 정제, SQL 로 어려운 가공에 써요",
             url=D + "dataflow/docs/overview"),
        dict(name="Managed Service for Apache Spark", sub="옛 Dataproc", icon=leg("dataproc"), dest="→ BigQuery · GCS",
             what="Spark 코드를 서버 관리 없이 실행", why="이미 있는 Spark 코드를 그대로 돌려요",
             url=D + "managed-spark/docs/serverless-overview"),
        dict(name="Cloud Data Fusion", sub="no-code ETL", icon=leg("cloud_data_fusion"), dest="→ BigQuery 등",
             what="화면에서 블록을 이어 만드는 ETL", why="코드 없이 파이프라인을 그려요",
             url=D + "data-fusion/docs/concepts/overview"),
    ]),
    ("쌓기", "Store", "목적에 맞는 저장소", [
        dict(name="Cloud Storage", sub="GCS · 데이터 레이크", icon=core("Cloud Storage", "Cloud_Storage-512-color.svg"), dest="원본 보관",
             what="어떤 파일이든 원본 그대로 두는 호수", why="싸고 크게, 나중에 다시 쓸 원본을 지켜요",
             url=D + "storage/docs/introduction"),
        dict(name="BigQuery", sub="BQ · 데이터 웨어하우스", icon=core("BigQuery", "BigQuery-512-color.svg"), dest="분석의 중심",
             what="SQL 로 대량 분석하는 서버리스 웨어하우스", why="거의 모든 길이 여기로 와요. 분석·AI 가 여기서 시작해요",
             url=D + "bigquery/docs/introduction", hero=True),
        dict(name="Lakehouse", sub="옛 BigLake · Iceberg", icon=cat("Data Analytics", "DataAnalytics-512-color.svg"), dest="옮기지 않고 조회",
             what="레이크 파일을 표처럼 다루는 층", why="GCS 의 Iceberg 테이블을 복사 없이 BigQuery 에서 읽어요",
             url=D + "lakehouse/docs/introduction"),
        dict(name="Bigtable", sub="key-value", icon=leg("bigtable"), dest="앱이 바로 읽기",
             what="row key 로 아주 빨리 읽는 저장소", why="실시간 앱·시계열에 데이터를 내줘요",
             url=D + "bigtable/docs/overview"),
    ]),
    ("쓰기", "Use", "사람과 AI 가 쓰게", [
        dict(name="Data Studio · Looker", sub="옛 Looker Studio", icon=core("Looker", "Looker-512-color.svg"), dest="사람이 보기",
             what="대시보드와 BI 리포트", why="숫자를 그림으로 보고 판단하게 해요",
             url=D + "data-studio"),
        dict(name="BigQuery ML · Gemini in BigQuery", sub="BQML", icon=cat("AI _ Machine Learning", "AIMachineLearning-512-color.svg"), dest="SQL 로 AI",
             what="BigQuery 안에서 SQL 로 ML·생성형 AI", why="데이터를 옮기지 않고 예측·요약해요",
             url=D + "bigquery/docs/bqml-introduction"),
        dict(name="Gemini Enterprise Agent Platform", sub="옛 Vertex AI", icon=core("Vertex AI", "VertexAI-512-color.svg"), dest="AI 서비스로",
             what="모델·RAG·에이전트를 만드는 플랫폼", why="정리된 데이터를 AI 서비스로 이어요",
             url=D + "gemini-enterprise-agent-platform"),
        dict(name="BigQuery sharing", sub="옛 Analytics Hub", icon=leg("analytics_hub"), dest="안팎에 나누기",
             what="데이터셋을 구독형으로 공유", why="복사하지 않고 다른 팀·회사와 나눠요",
             url=D + "bigquery/docs/analytics-hub-introduction"),
    ]),
]

DATAFORM = dict(name="Dataform", sub="ELT · 넣은 뒤 BigQuery 안에서 SQL 로 다듬기",
                what="BigQuery 안의 SQL 변환을 버전 관리·테스트·스케줄", why="Google 이 기본으로 권하는 ELT 방식이에요",
                url=D + "dataform/docs/overview")

BANDS = [
    ("자동화", "Orchestrate", "언제, 어떤 순서로", [
        dict(name="Managed Service for Apache Airflow", sub="옛 Cloud Composer", icon=leg("cloud_composer"),
             what="DAG 로 전체 단계를 지휘", why="여러 단계를 순서·재시도까지 한 번에 돌려요",
             url=D + "composer/docs/composer-3/composer-overview"),
        dict(name="Workflows", sub="", icon=leg("workflows"),
             what="서비스 호출 순서를 정의", why="몇 개 서비스를 가볍게 이어 부를 때 써요",
             url=D + "workflows/docs/overview"),
        dict(name="Cloud Scheduler", sub="cron", icon=leg("cloud_scheduler"),
             what="정해진 시각에 작업을 깨움", why="매일 새벽 같은 정기 작업을 시작해요",
             url=D + "scheduler/docs/overview"),
        dict(name="Cloud Run functions", sub="", icon=leg("cloud_functions"),
             what="이벤트에 반응하는 작은 코드", why="파일이 올라오면 바로 적재 같은 작은 일을 해요",
             url=D + "run/docs/functions/overview"),
        dict(name="Eventarc", sub="", icon=leg("eventarc"),
             what="이벤트를 받을 곳에 연결", why="무슨 일이 생기면 누구를 부를지 이어 줘요",
             url=D + "eventarc/docs/overview"),
    ]),
    ("지키기", "Govern", "누가, 무엇을, 믿을 수 있나", [
        dict(name="Knowledge Catalog", sub="옛 Dataplex", icon=leg("dataplex"),
             what="데이터 찾기·품질·계보", why="데이터가 어디 있고 믿을 만한지 알려줘요",
             url=D + "knowledge-catalog/docs/introduction"),
        dict(name="IAM", sub="Identity and Access Management", icon=leg("identity_and_access_management"),
             what="누가 무엇을 할 수 있는지", why="필요한 사람만 필요한 만큼 접근하게 해요",
             url=D + "iam/docs/overview"),
        dict(name="Sensitive Data Protection", sub="Cloud DLP 포함", icon=leg("data_loss_prevention_api"),
             what="개인정보를 찾아 가리기", why="민감한 값이 분석·AI 로 새지 않게 막아요",
             url=D + "sensitive-data-protection/docs/sensitive-data-protection-overview"),
    ]),
]

REFS = [
    ("Professional Data Engineer 시험 가이드", "https://services.google.com/fh/files/misc/professional_data_engineer_exam_guide_english.pdf"),
    ("Google Skills · Data Engineer learning path", "https://www.skills.google/paths/16"),
    ("ELT 와 ETL 고르기", D + "bigquery/docs/load-transform-export-intro"),
]

e = html.escape


def tip(c):
    return (f'<span class="tip" role="tooltip"><b>무엇</b>{e(c["what"])}'
            f'<b>왜</b>{e(c["why"])}</span>')


def card(c, link=True):
    cls = "card hero" if c.get("hero") else "card"
    sub = f'<span class="sub">{e(c["sub"])}</span>' if c.get("sub") else ""
    dest = f'<span class="dest">{e(c["dest"])}</span>' if c.get("dest") else ""
    inner = (f'<span class="nm">{e(c["name"])}</span>{sub}'
             f'<img class="ic" src="{uri(c["icon"])}" alt="" width="52" height="52">{dest}{tip(c)}')
    if c.get("hero"):
        df = DATAFORM
        inner += (f'</a><a class="df" href="{df["url"]}" target="_blank" rel="noopener">'
                  f'<span class="nm">{e(df["name"])}</span><span class="sub">{e(df["sub"])}</span>{tip(df)}')
        return f'<div class="herowrap"><a class="{cls}" href="{c["url"]}" target="_blank" rel="noopener">{inner}</a></div>'
    if link and c.get("url"):
        return f'<a class="{cls}" href="{c["url"]}" target="_blank" rel="noopener">{inner}</a>'
    return f'<div class="{cls} src" tabindex="0">{inner}</div>'


def chip(c):
    sub = f'<span class="sub">{e(c["sub"])}</span>' if c.get("sub") else ""
    return (f'<a class="chip" href="{c["url"]}" target="_blank" rel="noopener">'
            f'<img class="ic" src="{uri(c["icon"])}" alt="" width="36" height="36">'
            f'<span class="ct"><span class="nm">{e(c["name"])}</span>{sub}</span>{tip(c)}</a>')


cols = []
for i, (verb, en, hint, cards) in enumerate(STAGES):
    body = "".join(card(c, link=(i > 0)) for c in cards)
    if verb == "다듬기":
        body += ('<a class="elt" href="' + D + 'bigquery/docs/load-transform-export-intro" target="_blank" rel="noopener">'
                 '<span class="nm">또는 먼저 쌓고, BigQuery 안에서 다듬기</span>'
                 '<span class="sub">ELT · Google 기본 권장 → Dataform</span>'
                 '<span class="tip" role="tooltip"><b>무엇</b>원본을 먼저 BigQuery 에 넣고 SQL 로 가공해요'
                 '<b>왜</b>따로 가공 서버가 필요 없고, SQL 아는 사람이면 누구나 만들어요</span></a>')
    cols.append(f'<section class="stage s{i}"><header class="sh"><span class="dot">{i if i else ""}</span>'
                f'<h2>{e(verb)} <small>{e(en)}</small></h2><p>{e(hint)}</p></header>'
                f'<div class="cards">{body}</div></section>')

bands = []
for verb, en, hint, chips in BANDS:
    bands.append(f'<section class="band"><header><h2>{e(verb)} <small>{e(en)}</small></h2><p>{e(hint)}</p></header>'
                 f'<div class="chips">{"".join(chip(c) for c in chips)}</div></section>')

refs = "".join(f'<a href="{u}" target="_blank" rel="noopener">{e(t)}</a>' for t, u in REFS)

tpl = pathlib.Path(__file__).with_name("template.html").read_text(encoding="utf-8")
out = (tpl.replace("{{STAGES}}", "".join(cols)).replace("{{BANDS}}", "".join(bands)).replace("{{REFS}}", refs))
dest = pathlib.Path(sys.argv[1])
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text(out, encoding="utf-8")
print(dest, len(out))
