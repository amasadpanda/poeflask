import pydirectinput
import os
import threading
import time
import random
import asyncio

clientTxtFile = "D:\Games\Path of Exile\logs\LatestClient.txt"

keys = {
    'q' : {'type' : 'reuse', 'duration' : 2.9, 'skip-hideout': True},
    'w' : {'type' : 'once'},
    'f' : {'type' : 'once'},
    'p' : {'type' : 'once'},
    'b' : {'type' : 'once'},
    'g' : {'type' : 'once', 'skip-hideout': True},
#    'a' : {'type' : 'once', 'skip-hideout': True},
}

hideouts = {
    'Hideout' : False,
    'Karui Shores' : False,
    'The Sovereign' : False,
    'Kingsmarch' : False,
}

class ClientLogger:
    
    def __init__(self, txtFileLocation):
        self.file = txtFileLocation
        self.callbacks = {
            'load-location' : None,
            'in-location' : None,
            'focus' : None,
        }
        self.parser = {
            'You have entered ' : lambda l : self.callbacks['load-location'](l),
            '[LOADING SCREEN] (' : lambda l : self.callbacks['in-location'](l),
            '[WINDOW] Lost focus' : lambda l : self.callbacks['focus'](False),
            '[WINDOW] Gained focus' : lambda l : self.callbacks['focus'](True),
        }
        
    def readClientLog(self):
        with open(self.file, 'rb') as f_in:
            f_in.seek(0, os.SEEK_END)
            print('Read client log start')
            while True:
                # read last line of file
                line = f_in.readline()
                if not line.strip():
                    continue
                #print(f'READ: {line = }')
                loggedLine = str(line)
                for strings in self.parser:
                    if strings in loggedLine:
                        print(f'READ: {line = }')
                        self.parser[strings](loggedLine)
                    
    def start(self):
        parseClientThread = threading.Thread(target=self.readClientLog, args=())
        parseClientThread.start()
        
    def switchLocation(self, funct):
        self.callbacks['load-location'] = funct
        
    def onLocation(self, funct):
        self.callbacks['in-location'] = funct
        
    def onFocus(self, funct):
        self.callbacks['focus'] = funct
        

windowFocused = False

        
def windowFocusedChanged(focused):
    global windowFocused
    windowFocused = focused
    
async def waitForWindowFocused():
    while not windowFocused:
        time.sleep(.6)
    
async def pressKey(flask, hideout):
    global keys
    global windowFocused
    skipInHideout = keys[flask].get('skip-hideout', False)
    if(hideout and skipInHideout):
        return
    
    if not windowFocused:
        return
        
    pydirectinput.press(flask)
    print('Pressed ' + flask)
    
def triggerKeys(stop_event, hideout):
    global keys
    global windowFocused

    asyncio.run(waitForWindowFocused())
    
    print('Flasks Start')
        
    for flask in keys:
        match keys[flask]:
            case {'type' : 'once'}:
                asyncio.run(pressKey(flask, hideout))
            case _:
                pass
        
    count = {}
    while not stop_event.is_set():
        sleepFor = (random.random() / 2) + 0.7
        
        for flask in keys:
            match keys[flask]:
                case {'type' : 'reuse'}:
                    healthFlaskDuration = keys[flask]['duration']
                    skipInHideout = keys[flask]['skip-hideout']
                    count.setdefault(flask, 9999)
                    count[flask] += sleepFor
                    
                    if (count[flask] > healthFlaskDuration):
                        count[flask] = 0
                        asyncio.run(pressKey(flask, hideout))
                case _:
                    pass
                
        time.sleep(sleepFor)

stop_signal = threading.Event()
keysTriggerThread = None

def parseLocation(line):
    global keysTriggerThread
    global stop_signal
    inHideout = False
    for hideout in hideouts:
        if(hideout in line):
            inHideout = True
    stop_signal.clear()
    keysTriggerThread = threading.Thread(target=triggerKeys, args=(stop_signal, inHideout))
    keysTriggerThread.start()
    
def stopKeys(line):
    global keysTriggerThread
    global stop_signal
    stop_signal.set()
    if keysTriggerThread is not None:
        keysTriggerThread.join()

cl = ClientLogger(clientTxtFile)
cl.switchLocation(stopKeys)
cl.onLocation(parseLocation)
cl.onFocus(windowFocusedChanged)
cl.start()
