import oddvoices.frontend


def test_pronounce_text_basic():
    text = "hello world"
    expected = [
        ["_", "h", "@", "l"],
        ["oU", "_"],
        ["_", "w", "@`", "l", "d", "_"],
    ]
    assert oddvoices.frontend.pronounce_text(text) == expected
