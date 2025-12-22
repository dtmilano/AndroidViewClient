#! /usr/bin/env python3

from com.dtmilano.android.viewclient import ViewClient

helper = ViewClient.view_client_helper()
oid = helper.ui_device.find_object(ui_selector="desc@YouTube").oid
t, l, r, b = helper.ui_object.get_bounds(oid=oid)
s_x = int(l + (r - l)/2)
s_y = int(t + (b - t)/2)
e_x = 300
e_y = 700
helper.ui_device.drag(s_x, s_y, e_x, e_y, 50)
