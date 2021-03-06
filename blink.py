from __future__ import print_function
import io, json, os, requests, sys, yaml
from time import sleep
import dateutil.parser


__version__ = '0.3.0'

def save_to_file(content, filename):
    f = open(filename, 'wb')
    f.write(content)
    f.close()

def remove_info(filefrom, fileto):
    fw = open(fileto, "w")
    with open(filefrom) as f:
        end = True
        for line in f:
            if end:
                if line.find('```json') >= 0:
                    end = False
            else:
                if line.find('```') >= 0:
                    end = True

            if not end:
                index = line.find(':')
                hasbracket = line.find('{')
                hasinp = line.find('[')
                if index > 0 and hasbracket < 0 and hasinp < 0:
                    line = line[:index+1] + " xxx\n"
            fw.write(line)

    fw.close()

class Network(object):
    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)
    def __repr__(self):
        return '<Network id=%s name=%s>' % (self.id, repr(self.name))

class Event(object):
    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)
    def __repr__(self):
        return '<Event id=%s camera=%s at=%s>' % (self.id, repr(self.camera_name), repr(self.created_at))

class Video(object):
    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)
    def __repr__(self):
        return '<Video id=%s camera=%s at=%s>' % (self.id, repr(self.camera_name), repr(self.created_at))

class SyncModule(object):
    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)
    def __repr__(self):
        return '<SyncModule %s>' % repr(self.__dict__)

class Camera(object):
    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)
    def __repr__(self):
        return '<Camera id=%s name=%s>' % (self.id, repr(self.name))

###############################################################################
##  Blink API
###############################################################################

class Blink(object):

    def __init__(self, email, password, server='immedia-semi.com'):
        self._authtoken = None
        self._email = email
        self._password = password
        self._server = server
        self._region = 'prod'

###############################################################################
##  Property
###############################################################################
    @property
    def connected(self):
        return self._authtoken is not None

    @property
    def _auth_headers(self):
        return {'TOKEN_AUTH': self._authtoken['authtoken']}

###############################################################################
##  Common
###############################################################################
    def _connect_if_needed(self):
        if not self._authtoken: self.login()
        if not self.connected: raise Exception('Unable to connect.')

    def _path(self, path):
        return 'https://rest.%s.%s/%s' % (self._region, self._server, path.lstrip('/'))

    def get_event_name_v2(self, event):
        files = event.address.split('/')
        return event.camera_name + "_" + files[len(files)-1]

    def get_thumbnail_name_event(self, event, postfix=""):
        return self.get_event_name_v2(event) + postfix + ".jpg"

    def get_thumbnail_name_device(self, device, postfix=""):
        files = device['thumbnail'].split('/')
        return files[len(files)-1] + postfix + ".jpg"

###############################################################################
##  Highlighted Client APIs
###############################################################################
    def login(self):
        headers = {
            'Content-Type': 'application/json',
            'Host': "prod." + self._server,
        }
        data = {
            'email': self._email,
            'password': self._password,
            'client_specifier': 'iPhone 9.2 | 2.2 | 222',
        }
        resp = requests.post(self._path('login'), json=data, headers=headers)
        if resp.status_code!=200:
            raise Exception(resp.json()['message'])
        raw = resp.json()
        self._networks_by_id = raw['networks']
        self.networks = []
        for network_id, network in self._networks_by_id.items():
            network = dict(network)
            network['id'] = network_id
            network = Network(**network)
            self.networks.append(network)

        (self._region, value) = raw['region'].items()[0]
        self._authtoken = raw['authtoken']

    def cameras(self, network, type='motion'):
        self._connect_if_needed()
        resp = requests.get(self._path('network/%s/cameras' % network.id), headers=self._auth_headers)
        cameras = resp.json()['devicestatus']
        cameras = [Camera(**camera) for camera in cameras]
        return cameras

    def homescreen(self):
        '''
        Return information displayed on the home screen of the mobile client
        '''
        self._connect_if_needed()
        resp = requests.get(self._path('homescreen'), headers=self._auth_headers)
        return resp.json()

    def download_thumbnail_event_v2(self, event):
        '''
          returns the jpg data as a file-like object
        '''
        self._connect_if_needed()
        resp = requests.get(self._path(event.thumbnail+".jpg"), headers=self._auth_headers)
        return resp.content

    def download_thumbnail_home_v2(self, device):
        '''
          returns the jpg data as a file-like object
        '''
        self._connect_if_needed()
        filename = device['thumbnail']+".jpg"
        resp = requests.get(self._path(filename), headers=self._auth_headers)
        return resp.content, self.get_thumbnail_name_device(device)

    def eventsv2(self, pagenumber = 0):
        self._connect_if_needed()
        resp = requests.get(self._path('api/v2/videos/page/'+str(pagenumber)), headers=self._auth_headers)
        events = resp.json()
        events = [Event(**event) for event in events]
        return events

    def get_video_count(self):
        self._connect_if_needed()
        resp = requests.get(self._path('api/v2/videos/count'), headers=self._auth_headers)
        return resp.json()['count']

    def download_video_v2(self, event):
        '''
          returns the mp4 data as a file-like object
        '''
        self._connect_if_needed()
        resp = requests.get(self._path(event.address), headers=self._auth_headers)
        return resp.content

###############################################################################
##  Wrapped Functions
###############################################################################
    def list_network_ids(self):
        self._connect_if_needed()
        ids = []
        resp = requests.get(self._path("networks"), headers=self._auth_headers)
        resp = resp.json()
        for network in resp['networks']:
            if not resp['summary'][str(network['id'])]['onboarded']:
                continue
            ids.append(network['id'])
        return ids

    def list_camera_ids(self):
        ids = []
        resp = requests.get(self._path("networks"), headers=self._auth_headers)
        resp = resp.json()
        for network in resp['networks']:
            if not resp['summary'][str(network['id'])]['onboarded']:
                continue

            camurl = self._path("network/"+str(network['id'])+"/cameras")
            respcam = requests.get(camurl, headers=self._auth_headers)
            respcam = respcam.json()
            for camera in respcam['devicestatus']:
                ids.append(camera['camera_id'])

        return ids

    def refresh_all_cameras_thumbnail(self):
        '''
          Refresh all cameras with lastest thumbnails
        '''
        self._connect_if_needed()

        resp = requests.get(self._path("networks"), headers=self._auth_headers)
        resp = resp.json()
        for network in resp['networks']:
            if not resp['summary'][str(network['id'])]['onboarded']:
                continue
            camurl = self._path("network/"+str(network['id'])+"/cameras")
            respcam = requests.get(camurl, headers=self._auth_headers)
            respcam = respcam.json()
            for camera in respcam['devicestatus']:
                capurl = self._path("network/"+str(network['id'])+"/camera/"+str(camera['camera_id'])+"/thumbnail")
                rescap = requests.post(capurl, headers=self._auth_headers)
        sleep(1.5)
        return ;

    def refresh_all_cameras_video(self):
        '''
          Refresh all cameras with lastest thumbnails
        '''
        self._connect_if_needed()

        resp = requests.get(self._path("networks"), headers=self._auth_headers)
        resp = resp.json()
        for network in resp['networks']:
            if not resp['summary'][str(network['id'])]['onboarded']:
                continue
            camurl = self._path("network/"+str(network['id'])+"/cameras")
            respcam = requests.get(camurl, headers=self._auth_headers)
            respcam = respcam.json()
            for camera in respcam['devicestatus']:
                capurl = self._path("network/"+str(network['id'])+"/camera/"+str(camera['camera_id'])+"/clip")
                # print("capture video url: " + capurl)
                rescap = requests.post(capurl, headers=self._auth_headers).json()
                print("capture video output: " + str(rescap))

        sleep(8)
        return ;


    def events_from_camera(self, camera_id, max_count = 5):
        self._connect_if_needed()

        events = []
        pagenumber = -1
        while len(events) < max_count:
            pagenumber = pagenumber + 1
            resp = requests.get(self._path('api/v2/videos/page/'+str(pagenumber)), headers=self._auth_headers)
            currentEvents = resp.json()
            for event in currentEvents:
                if event['camera_id'] == camera_id:
                    events.append(Event(**event))
                    if(len(events) >= max_count):
                        break;
        return events


###############################################################################
##  Other Client APIs
###############################################################################
    def sync_modules(self, network):
        '''
          Response: JSON response containing information about the known state of the Sync module, most notably if it is online
          Notes: Probably not strictly needed but checking result can verify that the sync module is online and will respond to requests to arm/disarm, etc.
        '''
        self._connect_if_needed()
        resp = requests.get(self._path('network/%s/syncmodules' % network.id), headers=self._auth_headers)
        return [SyncModule(**resp.json()['syncmodule'])]

    def arm(self, network):
        '''
          Arm the given network (start recording/reporting motion events)
          Response: JSON response containing information about the disarm command request, including the command/request ID
          Notes: When this call returns, it does not mean the disarm request is complete, the client must gather the request ID from the response and poll for the status of the command.
        '''
        self._connect_if_needed()
        resp = requests.post(self._path('network/%s/arm' % network.id), headers=self._auth_headers)
        return resp.json()

    def disarm(self, network):
        '''
          Disarm the given network (stop recording/reporting motion events)
          Response: JSON response containing information about the disarm command request, including the command/request ID
          Notes: When this call returns, it does not mean the disarm request is complete, the client must gather the request ID from the response and poll for the status of the command.
        '''
        self._connect_if_needed()
        resp = requests.post(self._path('network/%s/disarm' % network.id), headers=self._auth_headers)
        return resp.json()

    def command_status(self, network, command_id):
        '''
          Get status info on the given command
          Response: JSON response containing state information of the given command, most notably whether it has completed and was successful.
          Notes: After an arm/disarm command, the client appears to poll this URL every second or so until the response indicates the command is complete.
          Known Commands: lv_relay, arm, disarm, thumbnail, clip
        '''
        self._connect_if_needed()
        resp = requests.get(self._path('network/%s/command/%s' % (network.id, command_id)), headers=self._auth_headers)
        return resp.json()

    def get_video_info(self, id):
        self._connect_if_needed()
        resp = requests.get(self._path('api/v2/video/'+str(id)), headers=self._auth_headers)
        return resp.json()

    def get_unwatched_videos(self):
        self._connect_if_needed()
        resp = requests.get(self._path('api/v2/videos/unwatched/page/0'), headers=self._auth_headers)
        videos = resp.json()
        videos = [Video(**video) for video in videos]
        return videos

    def delete_video(self, id):
        self._connect_if_needed()
        resp = requests.post(self._path('api/v2/video/'+str(id)+"/delete"), headers=self._auth_headers)
        return resp.json()['code'] == 704

    def get_camera_info(self):
        self._connect_if_needed()

        cameraInfos = []

        resp = requests.get(self._path("networks"), headers=self._auth_headers)
        resp = resp.json()
        for network in resp['networks']:
            if not resp['summary'][str(network['id'])]['onboarded']:
                continue
            camurl = self._path("network/"+str(network['id'])+"/cameras")
            respcam = requests.get(camurl, headers=self._auth_headers)
            respcam = respcam.json()
            for camera in respcam['devicestatus']:
                capurl = self._path("network/"+str(network['id'])+"/camera/"+str(camera['camera_id']))
                cameraInfo = requests.get(capurl, headers=self._auth_headers).json()
                cameraInfos.append(cameraInfo)

        return cameraInfos

    def get_camera_sensor_info(self):
        self._connect_if_needed()

        cameraSensorInfos = []

        resp = requests.get(self._path("networks"), headers=self._auth_headers)
        resp = resp.json()
        for network in resp['networks']:
            if not resp['summary'][str(network['id'])]['onboarded']:
                continue
            camurl = self._path("network/"+str(network['id'])+"/cameras")
            respcam = requests.get(camurl, headers=self._auth_headers)
            respcam = respcam.json()
            for camera in respcam['devicestatus']:
                capurl = self._path("network/"+str(network['id'])+"/camera/"+str(camera['camera_id']) + "/signals")
                cameraSensorInfo = requests.get(capurl, headers=self._auth_headers).json()
                cameraSensorInfo['network_id'] = network['id']
                cameraSensorInfo['camera_id'] = camera['camera_id']
                cameraSensorInfos.append(cameraSensorInfo)

        return cameraSensorInfos

    def clients(self):
        '''
          Request Gets information about devices that have connected to the blink service
          Response JSON response containing client information, including: type, name, connection time, user ID
        '''
        self._connect_if_needed()
        resp = requests.get(self._path('account/clients'), headers=self._auth_headers)
        return resp.json()

    def regions(self):
        '''
          Gets information about supported regions
        '''
        self._connect_if_needed()
        resp = requests.get(self._path('regions'), headers=self._auth_headers)
        return resp.json()


###############################################################################
##  Obsolete functions are neither not working or not tested!
###############################################################################
    def events(self, network, type='motion'):
        self._connect_if_needed()
        resp = requests.get(self._path('events/network/%s' % network.id), headers=self._auth_headers)
        events = resp.json()['event']
        if type: events = [e for e in events if e['type']=='motion']
        events = [Event(**event) for event in events]
        return events

    def download_video(self, event):
        '''
          returns the mp4 data as a file-like object
        '''
        self._connect_if_needed()
        resp = requests.get(self._path(event.video_url), headers=self._auth_headers)
        return resp.content

    def download_thumbnail(self, event):
        '''
          returns the jpg data as a file-like object
          doesn't work - server returns 404
        '''
        self._connect_if_needed()
        thumbnail_url = self._path(event.video_url[:-4] + '.jpg')
        resp = requests.get(thumbnail_url, headers=self._auth_headers)
        return resp.content

    def health(self):
        '''
          Gets information about system health
        '''
        self._connect_if_needed()
        resp = requests.get(self._path('health'), headers=self._auth_headers)
        return resp.json()

    def archive(self, path):
        self._connect_if_needed()
        for network in self.networks:
            network_dir = os.path.join(path, network['name'])
            if not os.path.isdir(network_dir):
                os.mkdir(network_dir)

            already_downloaded = set()
            for fn in os.listdir(network_dir):
                if not fn.endswith('.mp4'): continue
                fn = fn[:-4]
                event_id = int(fn.split(' - ')[0])
                already_downloaded.add(event_id)

            events = self.events(network['id'])
            for event in events:
                if event['id'] in already_downloaded: continue
                when = dateutil.parser.parse(event['created_at'])
                event_fn = os.path.join(network_dir, '%s - %s @ %s.mp4' % (event['id'], event['camera_name'], when.strftime('%Y-%m-%d %I:%M:%S %p %Z')))
                print('Saving:', event_fn)
                mp4 = self.download_video(event)
                with open(event_fn,'w') as f:
                    f.write(mp4)
