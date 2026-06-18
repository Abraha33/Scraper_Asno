from app.storage import avoid_duplicates


def test_avoid_duplicates_by_fields():
    rows = [
        {"report": "ventas", "id": "1", "value": 10},
        {"report": "ventas", "id": "1", "value": 10},
        {"report": "ventas", "id": "2", "value": 20},
    ]
    assert avoid_duplicates(rows, ("report", "id")) == [rows[0], rows[2]]

