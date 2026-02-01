import re

FORBIDDEN_KEYWORDS = {
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", 
    "CREATE", "GRANT", "REVOKE", "EXECUTE", "EXEC"
}

def validate_sql(query: str) -> tuple[bool, str | None]:
    if not query:
        return False, "Query cannot be empty"

    stripped_query = query.strip()
    upper_query = stripped_query.upper()
    
    for keyword in FORBIDDEN_KEYWORDS:
        pattern = rf"\b{keyword}\b"
        if re.search(pattern, upper_query):
            return False, f"Forbidden keyword detected: {keyword}"

    if "--" in stripped_query or "/*" in stripped_query or "*/" in stripped_query:
        return False, "SQL comments not allowed"
    
    temp_query = stripped_query.rstrip(";")
    if ";" in temp_query:
        return False, "Multiple statements not allowed"
    
    if not upper_query.startswith("SELECT"):
        return False, "Query must be a SELECT statement"
            
    return True, None
