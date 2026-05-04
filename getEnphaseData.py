# Python script to collect data from our Enphase Envoy controller 
# and post it to MQ in a useful manner


import json
import os
import sys
import datetime
import requests
from paho.mqtt.publish import multiple
import xml.etree.ElementTree as ET
import ssl
from time import sleep
import urllib3


def readConfig(cfgfile):
    option_dict = json.load(open(cfgfile,'r'))
    return option_dict


def getInfo(envoyname):
    serialNumber = None
    version = None
    target_url = f'https://{envoyname}/info'
    resp = requests.get(target_url, verify=False)
    if resp.status_code == 200:
        root = ET.fromstring(resp.content)
        serialNumber = [child.text for child in root.iter('sn')]
        versionstr = [child.text for child in root.iter('software')]
        if len(serialNumber) > 0:
            serialNumber = serialNumber[0]
        if len(versionstr) > 0:
            version = int(versionstr[0][:versionstr[0].find('.')][1:])

    return serialNumber, version

def getToken(cfg, renew=False):
    token = None
    if os.path.isfile(cfg['TOKFILE']):
        token = open(cfg['TOKFILE'],'r').read()
    if token is None or token=='' or len(token) < 5 or renew is True:
        print('getting token')
        data = {'user[email]': cfg['ENVOY_USER'], 'user[password]': cfg['ENVOY_PASSWORD']}
        res = requests.post('https://enlighten.enphaseenergy.com/login/login.json?', data=data)
        if res.status_code == 200:
            response_data = json.loads(res.text)
            data = {'session_id': response_data['session_id'], 'serial_num': cfg['SERIALNO'], 'username': cfg['ENVOY_USER']}
            res = requests.post('https://entrez.enphaseenergy.com/tokens', json=data)
            if res.status_code == 200:
                with open(cfg['TOKFILE'], 'w') as f:
                    f.write(res.text)
                return res.text
            else:
                print('unable to get token from entrez.enphaseenergy.com')
        else:
            print('unable to login to enlighten.enphaseenergy.com')
        return None
    else:
        return token


def is_json_valid(json_data):
    if isinstance(json_data, bytes):
        json_data = json_data.decode('utf-8', errors='replace')
    try:
        json.loads(json_data)
    except ValueError as e:
        return False
    return True


def getLiveData(cfg):
    token = getToken(cfg)

    url = f'https://{cfg["ENVOY_HOST"]}/ivp/livedata/status'
    headers = {"Authorization": "Bearer " + token}
    stream = requests.get(url, timeout=5, verify=False, headers=headers)
    if stream.status_code == 401:
        token = getToken(cfg, True)
        headers = {"Authorization": "Bearer " + token}
        stream = requests.get(url, timeout=5, verify=False, headers=headers)
    elif stream.status_code != 200:
        print('Failed connect to Envoy got ', stream)
    elif is_json_valid(stream.content):
        if stream.json()['connection']['sc_stream'] == 'disabled':
            url_activate=f'https://{cfg["ENVOY_HOST"]}/ivp/livedata/stream'
            print('Stream is not active, trying to enable')
            response_activate=requests.post(url_activate, verify=False, headers=headers, json={"enable": 1})
            if is_json_valid(response_activate.content):
                if response_activate.json()['sc_stream']=='enabled':
                    stream = requests.get(url, stream=True, timeout=5, verify=False, headers=headers)
                    print('Success, stream is active now')
                else:
                    print('Failed to activate stream ', response_activate.content)
            else:
                print('Invalid Json Response:', response_activate.content)
        else:
            return  stream.json()
        
    return None


if __name__ == '__main__':
    cfgfile = 'config.json'
    stopfile = 'envoy.stop'
    cfg = readConfig(cfgfile)
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    auth = {'username':cfg['MQTT_USER'], 'password': cfg['MQTT_PASSWORD']}
    clientid = 'enphase'
    if int(cfg['MQTT_PORT']) == 8883:
        tls = {'ca_certs':None, 'cert_reqs':ssl.CERT_REQUIRED, 'tls_version':ssl.PROTOCOL_TLS}
    else:
        tls = None

    serial, vers = getInfo(cfg['ENVOY_HOST'])
    cfg['SERIALNO'] = serial
    cfg['VERSION'] = vers
    cfg['TOKFILE'] = '.token'

    token = getToken(cfg)
    livedata = getLiveData(cfg)

    msgs = []    
    if livedata:
        meters = livedata['meters']
        meas_time = datetime.datetime.utcfromtimestamp(int(meters['last_update']))
        pv_watts = float(meters['pv']['agg_p_mw'])/1000
        storage_watts = float(meters['storage']['agg_p_mw'])/1000
        grid_watts = float(meters['grid']['agg_p_mw'])/1000
        load_watts = float(meters['load']['agg_p_mw'])/1000

        msgs.append(('envoy/pv_watts', pv_watts, 1))
        msgs.append(('envoy/storage_watts', storage_watts, 1))
        msgs.append(('envoy/grid_watts', grid_watts, 1))
        msgs.append(('envoy/load_watts', load_watts, 1))
        msgs.append(('envoy/lastupdate', meas_time.isoformat()))
        multiple(msgs=msgs, hostname=cfg['MQTT_HOST'], port=int(cfg['MQTT_PORT']), client_id=clientid, keepalive=60, auth=auth, tls=tls)
