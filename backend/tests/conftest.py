"""공통 테스트 픽스처 — SQLite 호환 DB 세션 생성."""

from sqlalchemy import text

from app.db.base import Base

# Document 모델에는 ARRAY(String), Vector(768) 등 SQLite 미지원 타입이 있다.
# documents 테이블만 SQLite 호환 DDL로 직접 생성한다.
_DOCUMENTS_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS documents (
    id CHAR(32) NOT NULL PRIMARY KEY,
    user_id CHAR(32) NOT NULL,
    conversation_id CHAR(32),
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    keywords TEXT,
    embedding TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""


def create_test_tables(conn) -> None:
    """SQLite 호환 테이블 생성 (동기).

    ARRAY/Vector 컬럼을 가진 documents 테이블은 Base.metadata에서 임시 제거 후
    직접 DDL로 생성한다.
    """
    doc_table = Base.metadata.tables.get("documents")
    if doc_table is not None:
        Base.metadata.remove(doc_table)
        try:
            Base.metadata.create_all(conn)
        finally:
            # 원본 메타데이터에 복원 — 다른 테스트/모듈에 영향 없도록
            Base.metadata._add_table(doc_table.name, doc_table.schema, doc_table)
    else:
        Base.metadata.create_all(conn)

    conn.execute(text(_DOCUMENTS_TABLE_DDL))
