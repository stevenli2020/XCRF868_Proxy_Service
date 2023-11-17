import websocket
import time
import json
import _thread
import requests
import os
import datetime  
import hashlib
import random

if "SERVICE_CONFIG" in os.environ:
    SERVICE_CONFIG = json.loads(os.environ["SERVICE_CONFIG"])
else: # default config when configuration is not available from env
    SERVICE_CONFIG = {"STATUS_REPORT_TIMEOUT_S":7,"DATA_REPORT_TIMEOUT_S":10,"DATA_REPORT_INTERVAL_S":30,"STATUS_REPORT_INTERVAL_S":600,"READER_IP":"192.168.0.155","READER_POWER":[25],"STATUS_ENDPOINT":"https://ONETIMEproxydev.azurewebsites.net/api/v1/statusevent","DATA_ENDPOINT":"https://ONETIMEproxydev.azurewebsites.net/api/v1/tagevent","SECRET_CHARACTER_KEY":"7Bf5mdnVt2SCMEvgFcJMk2rk20DVHj"}
    
SN = ""
IP = SERVICE_CONFIG["READER_IP"]
ANTENNA_POWER = SERVICE_CONFIG["READER_POWER"]
TAGS = {}
RAWTIMES = []
DATA_REPORT_OBJ = {
	"deviceCompany": "9a7c2b0e6f5710d1e972982ab6be52d3",
	"device.serial": "4C7525664050",
	"antenna.serial": "",
	"Offset": "8",
	"TimeSent": "2023-10-13 06:59:25.330Z",
	"RawTimes": [],
	"Hash": "",
	"RandomNum": ""
}
STATUS_OBJ = {
    "deviceCompany": "9a7c2b0e6f5710d1e972982ab6be52d3",
	"device.serial": "4C7525664050",
    "deviceID": "4C7525664050",
	"device.name": "",
	"antenna.serial": "",
	"Offset": "8",
	"TimeSent": "",
	"RandomNum": "",
	"Values": {
		"device.vendor": "Invengo",
		"device.version": "",
		"temp.internal": ""
	},
	"Hash": "14030956040584468898"
}


def on_message(socket, message): 
    global TAGS, RAWTIMES
    # print(message)
    m = json.loads(message)
    if "GenRead_AckTypeOk" in m:
        if m["GenRead_AckTypeOk"]["OpState"] == 0:
            # print(m["GenRead_AckTypeOk"])
            ANT = m["GenRead_AckTypeOk"]["Antenna"]
            EPC = m["GenRead_AckTypeOk"]["EPC"]
            RSSI = m["GenRead_AckTypeOk"]["RSSI"]
            TIME = int(time.time())
            # print(TIME,ANT,EPC,RSSI)
            if EPC not in TAGS:
                TAGS[EPC]={}
                TAGS[EPC]["F"]={'TIME':TIME, 'ANT':ANT}
                TAGS[EPC]["B"]={'TIME':TIME, 'ANT':ANT, 'RSSI':RSSI}
                TAGS[EPC]["L"]={'TIME':TIME, 'ANT':ANT}
            else:
                TAGS[EPC]["L"]={'TIME':TIME, 'ANT':ANT}
                if RSSI > TAGS[EPC]["B"]["RSSI"]:
                    TAGS[EPC]["B"]={'TIME':TIME, 'ANT':ANT, 'RSSI':RSSI}
                if TIME - TAGS[EPC]["F"]["TIME"] > 5:
                    DATA_FRAME_F = ("A"+datetime.datetime.fromtimestamp(TAGS[EPC]["F"]["TIME"]).strftime("%d%m%Y%H%M%S%f"))[:-3]+";F"+str(ANT)+EPC
                    DATA_FRAME_B = ("A"+datetime.datetime.fromtimestamp(TAGS[EPC]["B"]["TIME"]).strftime("%d%m%Y%H%M%S%f"))[:-3]+";B"+str(ANT)+EPC
                    DATA_FRAME_L = ("A"+datetime.datetime.fromtimestamp(TAGS[EPC]["L"]["TIME"]).strftime("%d%m%Y%H%M%S%f"))[:-3]+";L"+str(ANT)+EPC
                    RAWTIMES.append(DATA_FRAME_F)
                    RAWTIMES.append(DATA_FRAME_B)
                    RAWTIMES.append(DATA_FRAME_L)
                    del TAGS[EPC]
                    # print(RAWTIMES)
                    # print('\r\n')
            
    elif "SetAntennasPower_AckOk" in m:
        print("Set antenna power", ANTENNA_POWER)
    else:
        # print(message)
        # print('==============================\r\n')
        pass
        
            
def on_close(socket, close_status_code, close_msg):
    print("on_close args:")
    if close_status_code or close_msg:
        print("close status code: " + str(close_status_code))
        print("close message: " + str(close_msg))
        
def on_open(socket):
    global DATA_REPORT_OBJ,SERVICE_CONFIG,SN
    socket.send('{"CloseRfPower":{}}')
    time.sleep(1)
    n=0
    for p in SERVICE_CONFIG["READER_POWER"]:
        n=n+1
        socket.send('{"SetAntennasPower":{"Len":2,"Antenna":'+str(n)+',"dBm":'+str(p)+'}}');
        print("Set Antenna"+str(n)+" power "+str(p)+"dBm")
    
    print("Started...")
    socket.send('{"GenRead":{"Antennas":"00000001","Q":1,"OpType":1,"LenTid":0,"PointerUserEvb":0,"LenUser":0}}');

def post_events(url, body, timeout):
    print("Sending event to url =",url)
    try:
        x = requests.post(url, json = body, timeout=timeout)
        response = json.loads(x.text)
        print("- "+url,"\r\n- "+json.dumps(body)+"\r\n- ",response)       
    except requests.exceptions.RequestException as e:
        print("- POST REQ: "+url, "\r\n- Error: ", str(e))
        

def data_report_loop(threadName):
    global TAGS,RAWTIMES,SERVICE_CONFIG
    while 1:
        time.sleep(SERVICE_CONFIG["DATA_REPORT_INTERVAL_S"])
        if RAWTIMES:
            DATA_REPORT_OBJ['TimeSent'] = datetime.datetime.now().isoformat()
            DATA_REPORT_OBJ['RawTimes'] = RAWTIMES
            RAWTIMES_JSON = json.dumps(RAWTIMES)
            DATA_REPORT_OBJ['Hash'] = hashlib.md5((RAWTIMES_JSON+SERVICE_CONFIG["SECRET_CHARACTER_KEY"]).encode('utf-8')).hexdigest()
            RAWTIMES = []
            DATA_REPORT_OBJ['RandomNum'] = str(random.randrange(10000000,99999999))
            print('\r\n',json.dumps(DATA_REPORT_OBJ,indent=4))
            _thread.start_new_thread( post_events, (SERVICE_CONFIG["DATA_ENDPOINT"],DATA_REPORT_OBJ,SERVICE_CONFIG["DATA_REPORT_TIMEOUT_S"]))
        else:
            pass

def status_report_loop(threadName):
    global SERVICE_CONFIG,STATUS_OBJ
    time.sleep(2)
    while 1:
        print(json.dumps(STATUS_OBJ, indent=4))
        _thread.start_new_thread( post_events, (SERVICE_CONFIG["STATUS_ENDPOINT"],STATUS_OBJ, SERVICE_CONFIG["STATUS_REPORT_TIMEOUT_S"]))
        time.sleep(SERVICE_CONFIG["STATUS_REPORT_INTERVAL_S"])

def get_status_loop(threadName):
    global SERVICE_CONFIG,STATUS_OBJ
    time.sleep(1)
    while 1:
        url = 'http://'+SERVICE_CONFIG['READER_IP']+':5000/api/v1.0/general'
        try:
            x = requests.post(url, json = {'GetDeviceInfo': {'field_all': True}}, timeout=2)
        except requests.exceptions.RequestException as e:
            print("- POST REQ: "+url, "\r\n- Error: ", str(e)) 
            print("!!! \r\n\r\n <<< Reader not connected, restart >>>")
            os._exit(1)
        deviceInfo = json.loads(x.text)['GetDeviceInfo_AckOk']
        x = requests.post(url, json = {'GetSystemResourceInfoAll': {'field_all': True}})
        systemResourceInfoAll = json.loads(x.text)['GetSystemResourceInfoAll_AckOk']
        # print(deviceInfo)
        # print(systemResourceInfoAll)
        STATUS_OBJ['TimeSent'] = datetime.datetime.now().isoformat()
        STATUS_OBJ['device.name'] = deviceInfo['devicename']
        STATUS_OBJ['Values']['reader.serial'] = deviceInfo['sn']
        STATUS_OBJ['Values']['device.name'] = deviceInfo['devicename']
        STATUS_OBJ['Values']['device.version'] = deviceInfo['version_mcu']+","+deviceInfo['version_ws_server_irp']
        STATUS_OBJ['Values']['temp.internal'] = systemResourceInfoAll['Temprature']
        STATUS_OBJ['Values']['cpu.internal'] = systemResourceInfoAll['CpuUse']
        STATUS_OBJ['Values']['memory.internal'] = systemResourceInfoAll['MemoryUse']
        STATUS_OBJ['Values']['disk.internal'] = systemResourceInfoAll['DiskAvailable']
        STATUS_OBJ['RandomNum'] = str(random.randrange(10000000,99999999))
        STATUS_OBJ['Hash'] = hashlib.md5((json.dumps(STATUS_OBJ['Values'])+SERVICE_CONFIG["SECRET_CHARACTER_KEY"]).encode('utf-8')).hexdigest()
        print(json.dumps(STATUS_OBJ, indent=4))
        if SERVICE_CONFIG["STATUS_REPORT_TIMEOUT_S"] / 10 >= 10: # this is to ensure minimum status polling interval will be greater than 10 seconds
            time.sleep(SERVICE_CONFIG["STATUS_REPORT_TIMEOUT_S"]/10)
        else:
            time.sleep(10) 

def main():
    while 1:
        try:
            print("Connecting to reader @"+SERVICE_CONFIG['READER_IP'])
            url = 'http://'+SERVICE_CONFIG['READER_IP']+':5000/api/v1.0/general'
            x = requests.post(url, json = {'GetDeviceInfo': {'field_all': True}}, timeout=3)
            response = json.loads(x.text)
            SN = ""
            if "GetDeviceInfo_AckOk" in response:
                SN = response["GetDeviceInfo_AckOk"]["sn"]
            print("Reader connected, SN = "+SN)    
            DATA_REPORT_OBJ['reader.serial'] = SN
            break            
        except:
            print("Reader not connected, retry after 2 seconds")
            time.sleep(2)
            pass

    _thread.start_new_thread( data_report_loop, ("svc",)) # thread to post data reports
    _thread.start_new_thread( status_report_loop, ("report_status",)) # thread to post status reports
    _thread.start_new_thread( get_status_loop, ("get_status",)) # thread to get status periodically
    wsapp = websocket.WebSocketApp("ws://"+IP+":7681", on_message=on_message, on_close=on_close, on_open=on_open)
    wsapp.run_forever() 
    
if __name__ == "__main__":
    main()