import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
FILES = [
    f
    for f in subprocess.run(["git", "-C", str(ROOT), "ls-files", "-co", "--exclude-standard"], capture_output=True, text=True).stdout.split()
    if (ROOT / f).is_file()
]
TEXT = [f for f in FILES if re.search(r"\.(py|md|json|toml|ya?ml)$", f)]

sys.path.insert(0, str(ROOT))
from scripts import check_brands  # noqa: E402
from tokacct.pii import redact  # noqa: E402


def test_brand_check_clean():
    assert check_brands.scan(ROOT, FILES) == []


def test_brand_check_detects():
    term = "Zzyzx Corp"
    hits = check_brands.find_hits("we use Zzyzx Corp here", {check_brands.digest(term.lower())}, {check_brands.digest(term)})
    assert hits == [term]


def test_no_pii_in_tracked_text():
    for f in TEXT:
        if f.startswith("tests/") or f == "src/tokacct/pii.py":
            continue
        txt = (ROOT / f).read_text(errors="ignore")
        assert redact(txt) == txt, f
