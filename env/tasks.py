from env.models import FindingSpec, TaskSpec


TASKS = {
    "easy": TaskSpec(
        task_id="cr-001",
        task_type="easy",
        title="PEP8 and maintainability review",
        objective="Identify style and readability defects in a utility function.",
        code=(
            "def calculate_total(prices,tax_rate):\n"
            " total=0\n"
            " for p in prices: total += p\n"
            " return total+total*tax_rate\n"
        ),
        max_steps=4,
        expected_findings=[
            FindingSpec(
                finding_id="easy-spacing",
                description="Missing spacing around commas/operators and poor formatting.",
                expected_line=1,
                keywords=["spacing", "pep8", "format", "readability"],
            ),
            FindingSpec(
                finding_id="easy-docstring",
                description="Function lacks a docstring explaining parameters/return value.",
                expected_line=1,
                keywords=["docstring", "documentation", "comment"],
            ),
        ],
    ),
    "medium": TaskSpec(
        task_id="cr-002",
        task_type="medium",
        title="Performance and correctness review",
        objective="Review data processing logic for efficiency and fault tolerance.",
        code=(
            "def load_active_users(rows):\n"
            " active=[]\n"
            " for r in rows:\n"
            "  if r['status']=='active':\n"
            "   active.append({'id':r['id'],'email':r['email'].lower()})\n"
            " return active\n"
        ),
        max_steps=5,
        expected_findings=[
            FindingSpec(
                finding_id="med-keyerror",
                description="Direct dictionary indexing can raise KeyError on missing fields.",
                expected_line=4,
                keywords=["keyerror", "missing key", "get(", "validation"],
            ),
            FindingSpec(
                finding_id="med-comprehension",
                description="Loop can be simplified into list comprehension for readability.",
                expected_line=3,
                keywords=["list comprehension", "readability", "refactor"],
            ),
            FindingSpec(
                finding_id="med-normalization",
                description="Email normalization should guard against non-string or null values.",
                expected_line=5,
                keywords=["null", "none", "sanitize", "lower()", "type check"],
            ),
        ],
    ),
    "hard": TaskSpec(
        task_id="cr-003",
        task_type="hard",
        title="Security-focused API review",
        objective="Detect security vulnerabilities and unsafe coding practices in auth logic.",
        code=(
            "import jwt\n"
            "\n"
            "def verify(token, secret):\n"
            " payload = jwt.decode(token, secret, options={'verify_signature': False})\n"
            " if payload.get('role') == 'admin':\n"
            "  return True\n"
            " return False\n"
        ),
        max_steps=6,
        expected_findings=[
            FindingSpec(
                finding_id="hard-signature",
                description="Token signature verification is disabled.",
                expected_line=4,
                keywords=["verify_signature", "signature", "jwt", "security"],
            ),
            FindingSpec(
                finding_id="hard-algorithm",
                description="JWT algorithm is not restricted and should be explicitly enforced.",
                expected_line=4,
                keywords=["algorithm", "alg", "allowlist", "jwt"],
            ),
            FindingSpec(
                finding_id="hard-authorization",
                description="Authorization logic trusts token role claim without issuer/audience checks.",
                expected_line=5,
                keywords=["issuer", "audience", "authorization", "claim", "role"],
            ),
        ],
    ),
}


TASK_ORDER = ["easy", "medium", "hard"]