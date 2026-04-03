"""Split tenant DDL into executable statements for asyncpg."""


def split_sql_statements(sql: str) -> list[str]:
    """Split SQL file on semicolons; skip empty chunks and line comments-only chunks."""
    parts: list[str] = []
    buf: list[str] = []
    for line in sql.splitlines():
        stripped = line.strip()
        if stripped.startswith("--"):
            continue
        buf.append(line)
    text = "\n".join(buf)
    for chunk in text.split(";"):
        stmt = chunk.strip()
        if stmt:
            parts.append(stmt + ";")
    return parts
