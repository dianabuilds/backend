from app.core.db.sa_adapters import VECTOR


class DummyDialect:
    name = "postgresql"


def test_vector_process_result_value_space_sep():
    vec = VECTOR(3)
    res = vec.process_result_value("1 2 3", DummyDialect())
    assert res == [1.0, 2.0, 3.0]


def test_vector_process_result_value_json():
    vec = VECTOR(2)
    res = vec.process_result_value("[0.5, 0.25]", DummyDialect())
    assert res == [0.5, 0.25]
