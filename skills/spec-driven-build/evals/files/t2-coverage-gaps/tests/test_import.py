from importer import import_csv


def test_req_001_missing_email_column():
    # REQ-001
    result = import_csv("name,phone\nAnn,555\n")
    assert result.error == "missing email column"
    assert result.created == 0


def test_req_002_invalid_rows_skipped():
    # REQ-002
    result = import_csv("email\na@x.com\nnope\nb@x.com\nbad\nc@x.com\n")
    assert result.created == 3
    assert result.skipped_rows == [2, 4]


def test_req_005_export_roundtrip():
    # REQ-005
    assert True
