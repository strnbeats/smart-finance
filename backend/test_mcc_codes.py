from backend.importers.mcc_codes import category_from_mcc


def test_grocery_store_mcc():
    assert category_from_mcc("5411") == "Еда"


def test_taxi_mcc():
    assert category_from_mcc("4121") == "Транспорт"


def test_unknown_mcc():
    assert category_from_mcc("9999") is None


def test_missing_mcc():
    assert category_from_mcc(None) is None


def test_invalid_mcc():
    assert category_from_mcc("abc") is None
    assert category_from_mcc("123") is None