import re
import sys

# ==========================================================
# ERROR HANDLER
# ==========================================================

def syntax_error(message, query=None, position=None, suggestion=None):
    print("\n❌ SYNTAX ERROR")
    print("➡", message)

    if query is not None:
        print("\n🔎 Query:")
        print(" ", query)

        if position is not None:
            print(" ", " " * position + "^")
            print(f"   Error at position {position}")

    if suggestion:
        print("\n💡 Suggestion:", suggestion)

    sys.exit(1)


# ==========================================================
# INPUT & NORMALIZATION
# ==========================================================

query = input("Enter SQL query:\n").strip()

if not query:
    syntax_error("Empty query", suggestion="Enter a valid SQL statement")

original_query = query
query = re.sub(r'\s+', ' ', query)

if not query.endswith(";"):
    syntax_error(
        "Missing semicolon at end of query",
        original_query,
        len(original_query),
        "Add ';' at the end"
    )

query = query[:-1]  # remove semicolon
ast = {}

# ==========================================================
# CREATE TABLE
# ==========================================================

if query.upper().startswith("CREATE TABLE"):
    ast["type"] = "CREATE_TABLE"

    m = re.match(r'CREATE TABLE (\w+)\s*\((.*)\)$', query, re.IGNORECASE)
    if not m:
        syntax_error(
            "Invalid CREATE TABLE syntax",
            original_query,
            0,
            "CREATE TABLE table_name (column datatype, ...);"
        )

    ast["table"] = m.group(1)
    ast["columns"] = {}
    ast["constraints"] = []

    parts = [p.strip() for p in m.group(2).split(",")]

    for p in parts:
        if p.upper().startswith(("PRIMARY", "FOREIGN", "UNIQUE", "CHECK")):
            ast["constraints"].append(p)
        else:
            c = p.split()
            if len(c) < 2:
                pos = original_query.find(p)
                syntax_error(
                    f"Invalid column definition near '{p}'",
                    original_query,
                    pos,
                    "Use: column_name datatype"
                )
            ast["columns"][c[0]] = c[1]

# ==========================================================
# DROP TABLE
# ==========================================================

elif query.upper().startswith("DROP TABLE"):
    ast["type"] = "DROP_TABLE"

    m = re.match(r'DROP TABLE (\w+)$', query, re.IGNORECASE)
    if not m:
        syntax_error(
            "Invalid DROP TABLE syntax",
            original_query,
            0,
            "DROP TABLE table_name;"
        )

    ast["table"] = m.group(1)

# ==========================================================
# ALTER TABLE
# ==========================================================

elif query.upper().startswith("ALTER TABLE"):
    ast["type"] = "ALTER_TABLE"

    m = re.match(r'ALTER TABLE (\w+)\s+(.*)$', query, re.IGNORECASE)
    if not m:
        syntax_error(
            "Invalid ALTER TABLE syntax",
            original_query,
            0,
            "ALTER TABLE table_name <action>;"
        )

    ast["table"] = m.group(1)
    action = m.group(2)

    if re.match(r'ADD \w+ \w+', action, re.IGNORECASE):
        a = re.match(r'ADD (\w+) (\w+)', action, re.IGNORECASE)
        ast["action"] = {"type": "ADD_COLUMN", "column": a.group(1), "datatype": a.group(2)}

    elif re.match(r'DROP COLUMN \w+$', action, re.IGNORECASE):
        a = re.match(r'DROP COLUMN (\w+)', action, re.IGNORECASE)
        ast["action"] = {"type": "DROP_COLUMN", "column": a.group(1)}

    elif re.match(r'DROP CONSTRAINT \w+$', action, re.IGNORECASE):
        a = re.match(r'DROP CONSTRAINT (\w+)', action, re.IGNORECASE)
        ast["action"] = {"type": "DROP_CONSTRAINT", "constraint": a.group(1)}

    elif re.match(r'RENAME COLUMN \w+ TO \w+$', action, re.IGNORECASE):
        a = re.match(r'RENAME COLUMN (\w+) TO (\w+)', action, re.IGNORECASE)
        ast["action"] = {"type": "RENAME_COLUMN", "old": a.group(1), "new": a.group(2)}

    elif re.match(r'RENAME TO \w+$', action, re.IGNORECASE):
        a = re.match(r'RENAME TO (\w+)', action, re.IGNORECASE)
        ast["action"] = {"type": "RENAME_TABLE", "new_name": a.group(1)}

    else:
        pos = original_query.upper().find(action.upper())
        syntax_error(
            f"Unsupported ALTER TABLE action '{action}'",
            original_query,
            pos,
            "ADD | DROP COLUMN | DROP CONSTRAINT | RENAME COLUMN | RENAME TO"
        )

# ==========================================================
# UPDATE
# ==========================================================

elif query.upper().startswith("UPDATE"):
    ast["type"] = "UPDATE"

    m = re.match(r'UPDATE (\w+)\s+SET (.*)$', query, re.IGNORECASE)
    if not m:
        syntax_error(
            "Invalid UPDATE syntax",
            original_query,
            0,
            "UPDATE table_name SET column=value WHERE condition;"
        )

    ast["table"] = m.group(1)
    rest = m.group(2)

    if " WHERE " in rest.upper():
        set_part, where_part = re.split(r'\bWHERE\b', rest, flags=re.IGNORECASE)
    else:
        set_part, where_part = rest, None

    ast["set"] = {}

    for assign in [a.strip() for a in set_part.split(",")]:
        if "=" not in assign:
            pos = original_query.find(assign)
            syntax_error(
                f"Invalid SET expression '{assign}'",
                original_query,
                pos,
                "Use: column = value"
            )
        col, val = assign.split("=", 1)
        ast["set"][col.strip()] = val.strip()

    ast["where"] = where_part.strip() if where_part else None
    ast["nested_query"] = bool(where_part and "SELECT" in where_part.upper())

# ==========================================================
# DELETE
# ==========================================================

elif query.upper().startswith("DELETE"):
    ast["type"] = "DELETE"

    m = re.match(r'DELETE FROM (\w+)$', query, re.IGNORECASE)
    if not m and " WHERE " not in query.upper():
        syntax_error(
            "Invalid DELETE syntax",
            original_query,
            0,
            "DELETE FROM table_name WHERE condition;"
        )

    table_match = re.match(r'DELETE FROM (\w+)', query, re.IGNORECASE)
    if not table_match:
        syntax_error("Missing table name in DELETE", original_query, 0)

    ast["table"] = table_match.group(1)

    where = re.search(r'WHERE (.*)$', query, re.IGNORECASE)
    ast["where"] = where.group(1) if where else None
    ast["nested_query"] = bool(where and "SELECT" in where.group(1).upper())

# ==========================================================
# SELECT (SAFE VERSION)
# ==========================================================

elif query.upper().startswith("SELECT"):
    ast["type"] = "SELECT"

    if " FROM " not in query.upper():
        syntax_error(
            "Missing FROM clause in SELECT",
            original_query,
            original_query.upper().find("SELECT") + 6,
            "SELECT column_name FROM table_name;"
        )

    m = re.match(r'SELECT\s+(.*?)\s+FROM\s+(.+)$', query, re.IGNORECASE)

    if not m:
        syntax_error(
            "Invalid SELECT syntax",
            original_query,
            0,
            "SELECT column_name FROM table_name;"
        )

    select_part = m.group(1).strip()
    from_part = m.group(2).strip()

    if not select_part:
        pos = original_query.upper().find("SELECT") + 6
        syntax_error(
            "Missing column list after SELECT",
            original_query,
            pos,
            "SELECT column_name FROM table_name;"
        )

    tables = re.findall(r'\b\w+\b', from_part)

    if not tables:
        pos = original_query.upper().find("FROM") + 4
        syntax_error(
            "Missing table name after FROM",
            original_query,
            pos,
            "SELECT column_name FROM table_name;"
        )

    ast["select"] = select_part
    ast["from"] = tables

# ==========================================================
# UNSUPPORTED
# ==========================================================

else:
    syntax_error(
        "Unsupported SQL statement",
        original_query,
        0,
        "Supported: CREATE, DROP, ALTER, SELECT, UPDATE, DELETE"
    )

# ==========================================================
# CLEAN OUTPUT
# ==========================================================

print("\n==============================")

if ast["type"] == "CREATE_TABLE":
    print("✅ CREATE TABLE parsed successfully!")
    print("Table Name:", ast["table"])
    print("Columns:")
    for col, dtype in ast["columns"].items():
        print(f" - {col} : {dtype}")
    if ast["constraints"]:
        print("Constraints:")
        for c in ast["constraints"]:
            print(f" - {c}")

elif ast["type"] == "DROP_TABLE":
    print("✅ DROP TABLE parsed successfully!")
    print("Table:", ast["table"])

elif ast["type"] == "ALTER_TABLE":
    print("✅ ALTER TABLE parsed successfully!")
    print("Table:", ast["table"])
    print("Action:", ast["action"])

elif ast["type"] == "UPDATE":
    print("✅ UPDATE parsed successfully!")
    print("Table:", ast["table"])
    print("SET:")
    for col, val in ast["set"].items():
        print(f" - {col} = {val}")
    if ast["where"]:
        print("WHERE:", ast["where"])
    if ast["nested_query"]:
        print("⚠ Nested SELECT detected")

elif ast["type"] == "DELETE":
    print("✅ DELETE parsed successfully!")
    print("Table:", ast["table"])
    if ast["where"]:
        print("WHERE:", ast["where"])
    if ast["nested_query"]:
        print("⚠ Nested SELECT detected")

elif ast["type"] == "SELECT":
    print("✅ SELECT parsed successfully!")
    print("Columns:", ast["select"])
    print("From:")
    for t in ast["from"]:
        print(f" - {t}")

print("==============================")