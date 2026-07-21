from scripts.project_readiness_check import check_required_files, scan_disallowed_terms


def test_required_project_files_exist():
    missing = check_required_files()

    assert missing == []


def test_no_legacy_terms_present():
    findings = scan_disallowed_terms()

    assert findings == []
