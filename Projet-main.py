from microbit import *
import radio
radio.config(channel = 1)
radio.on()
import time

def allumage_baby_parent():
    while True:
        message = radio.receive()
        if pin_logo.is_touched():   # be:bi parent allumé
            start = running_time()      
            while pin_logo.is_touched():
                if running_time() - start >= 3000:  
                    display.show('P')
                    break
            sleep(1000)
            radio.send('B')
        elif message:        #envoie vers le be:bi enfant
            display.show(message)
            sleep(1000)
            display.clear()
        else:
            display.clear()
