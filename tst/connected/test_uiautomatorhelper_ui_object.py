def test_exists(helper, calculator, oid_digit):
    assert helper.ui_object.exists(oid=oid_digit)


def test_get_child_count(helper, calculator, oid_group):
    response: int = helper.ui_object.get_child_count(oid=oid_group)
    assert response > 0


def test_perform_two_pointer_gesture(helper, calculator, oid_group):
    helper.ui_object.perform_two_pointer_gesture(oid_group, (0, 200), (100, 100), (100, 100), (0, 200), 10)


def test_pinch_in(helper, calculator, oid_digit):
    helper.ui_object.pinch_in(oid_digit, 5)


def test_pinch_out(helper, calculator, oid_digit):
    helper.ui_object.pinch_out(oid_digit, 5)
