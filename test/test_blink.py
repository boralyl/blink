from __future__ import print_function

import json
import os
import sys
import unittest

import requests_mock

import blink
from blink import Blink


def get_mock_response(response_filename):
    pth = os.path.join(
        os.path.dirname(__file__), 'mock_responses', response_filename)
    with open(pth) as fp:
        return json.load(fp)


###############################################################################
##  Unittests for Blink Client APIs
###############################################################################
class TestBlink(unittest.TestCase):
    email = ""
    password = ""

    def setUp(self):
        self.b = Blink(self.email, self.password)
        with requests_mock.Mocker() as m:
            m.post('https://rest.prod.immedia-semi.com/login',
                   json=get_mock_response('login.json'))
            self.b.login()

###############################################################################
##  Highlighted Client APIs
###############################################################################
    def test_login(self):
        self.assertTrue(self.b.connected)

    @requests_mock.Mocker()
    def test_homescreen(self, m):
        m.get('https://rest.u001.immedia-semi.com/homescreen',
              json=get_mock_response('homescreen.json'))
        m.get('https://rest.u001.immedia-semi.com/media/u001/account/1/network'
              '/1/camera/1/clip_foobar__2018_11_24__05_15AM.jpg', text='')

        data = self.b.homescreen()
        self.assertTrue(data['account'] is not None)
        self.assertTrue(data['network'] is not None)
        for device in data['devices']:
            if device['device_type'] is not None and device['device_type'] == "camera":
                content,filename = self.b.download_thumbnail_home_v2(device)
                blink.save_to_file(content, "home_"+filename)

    def test_events_v2(self):
        events = self.b.eventsv2()
        self.assertEqual(type(events), list)

    def test_video_count(self):
        count = self.b.get_video_count()
        print("video count = " + str(count))

    def test_events_v2_download(self):
        events = self.b.eventsv2()
        if len(events) == 0:
            return ;
        event = events[0]
        content = self.b.download_video_v2(event)
        filename = self.b.get_event_name_v2(event)
        blink.save_to_file(content, "event_"+filename)

    def test_thumbnail_event_v2_download(self):
        events = self.b.eventsv2()
        if len(events) == 0:
            return ;
        event = events[0]
        content = self.b.download_thumbnail_event_v2(event)
        filename = self.b.get_thumbnail_name_event(event, "event")
        f = open(filename, 'wb')
        f.write(content)
        f.close()
        print('Save downloaded image to ' + filename)

###############################################################################
##  Wrapped Functions
###############################################################################
    def test_list_network_ids(self):
        ids = self.b.list_network_ids()
        self.assertEqual(type(ids), list)

    def test_list_camera_ids(self):
        ids = self.b.list_camera_ids()
        self.assertEqual(type(ids), list)

    def test_events_from_camera(self):
        ids = self.b.list_camera_ids()
        if len(ids) > 0:
            id = ids[0]
            events = self.b.events_from_camera(id, 1)
            if len(events) > 0:
                event = events[0]
                content = self.b.download_video_v2(event)
                filename = self.b.get_event_name_v2(event)
                blink.save_to_file(content, "event_camera_"+filename)
    def test_refresh_all_cameras_thumbnail(self):
        self.b.refresh_all_cameras_thumbnail()
        data = self.b.homescreen()
        for device in data['devices']:
            if device['device_type'] is not None and device['device_type'] == "camera":
                content,filename = self.b.download_thumbnail_home_v2(device)
                filename = "test_refresh_" + filename
                blink.save_to_file(content, filename)
                print("Download latest thumbnails to " + filename)

###############################################################################
##  Other Client APIs
###############################################################################
    def test_cameras(self):
        cameras = self.b.cameras(self.b.networks[0])
        self.assertEqual(type(cameras), list)

    def test_clients(self):
        clients = self.b.clients()
        self.assertTrue(clients['clients'] is not None)
        print(clients)

    def test_sync_modules(self):
        sync_modules = self.b.sync_modules(self.b.networks[0])
        print(sync_modules)

    def test_regions(self):
        regions = self.b.regions()
        print(regions)

    def test_get_video_info(self):
        events = self.b.eventsv2()
        if len(events) == 0:
            return ;
        event = events[0]
        eventinfo = self.b.get_video_info(event.id)
        print("eventinfo:" + str(eventinfo))

    def test_delete_video(self):
        events = self.b.eventsv2(1000)
        if len(events) == 0:
            return ;
        event = events[len(events)-1]
        suc = self.b.delete_video(event.id)
        self.assertTrue(suc)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        TestBlink.password = sys.argv.pop()
        TestBlink.email = sys.argv.pop()
    unittest.main()
