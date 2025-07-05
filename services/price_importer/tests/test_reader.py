from services.price_importer.reader import detect_format, load_file


def test_detect_format():
    assert detect_format("foo.csv") == "csv"
    assert detect_format("foo.xlsx") == "excel"


def test_load_file_csv(tmp_path):
    p = tmp_path / "test.csv"
    p.write_text("a,b\n1,2\n")
    df = load_file(p)
    assert df.shape == (1, 2)


def test_load_file_xlsx(sample_xlsx):
    df = load_file(sample_xlsx)
    assert not df.empty
