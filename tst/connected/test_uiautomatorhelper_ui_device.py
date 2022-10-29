import threading
import time

from culebratester_client import WindowHierarchy, ObjectRef


def test_click(helper):
    helper.ui_device.click(100, 100)


def test_dump_window_hierarchy__json(helper):
    response = helper.ui_device.dump_window_hierarchy(_format='JSON')
    assert type(response) == WindowHierarchy


def test_dump_window_hierarchy__xml(helper):
    try:
        response = helper.ui_device.dump_window_hierarchy(_format='XML')
        assert type(response) == bytes
    except:
        pass


def test_find_object(helper, calculator):
    response = helper.ui_device.find_object(ui_selector='res@com.google.android.calculator:id/digit_9')
    assert type(response) == ObjectRef
    assert response.oid > 0


def test_find_objects(helper, calculator):
    response = helper.ui_device.find_objects(by_selector='package@com.google.android.calculator')
    assert type(response) == list
    assert len(response) > 0


def test_has_object(helper, calculator):
    assert helper.ui_device.has_object(by_selector='package@com.google.android.calculator')


def test_press_back(helper, calculator):
    helper.ui_device.press_back()


def test_press_enter(helper, calculator):
    helper.ui_device.press_enter()


def test_press_home(helper, calculator):
    helper.ui_device.press_home()


def test_press_recent_apps(helper, calculator):
    helper.ui_device.press_recent_apps()


def test_press_key_code(helper, calculator):
    helper.ui_device.press_key_code(25)  # volume down


def test_swipe(helper, calculator):
    helper.ui_device.swipe(start_x=0, start_y=500, end_x=800, end_y=500, steps=50)


def test_take_screenshot__filename(helper, calculator, tmp_path):
    helper.ui_device.take_screenshot(filename=f'{tmp_path}/sc1.png')


def test_wait(helper, calculator):
    search_condition_ref = helper.until.find_object(body={'desc': 'pi'})
    helper.ui_device.wait(search_condition_ref.oid, 5000)


def test_wait_for_idle(helper, calculator):
    helper.ui_device.wait_for_idle(timeout=5000)


def test_wait_for_window_update(helper, calculator):
    def delayed_press_keycode():
        time.sleep(3)
        helper.ui_device.press_key_code(16)

    threading.Thread(target=delayed_press_keycode).start()
    time.sleep(2)
    helper.ui_device.wait_for_window_update(timeout=8000, package_name='com.google.android.calculator')
