from microbit import *
import radio
radio.config(channel = 1)
radio.on()
import time
import music

def allumage_baby_parent():
    while True:
        message = radio.receive()
        if pin_logo.is_touched():   # be:bi parent allumé
            start = running_time()      
            while pin_logo.is_touched():
                if running_time() - start >= 3000:  
                    display.show('P')
                    break
            sleep(2000)
            radio.send('B')
            display.clear()
        elif message:        #envoie vers le be:bi enfant
            display.show(message)
            sleep(2000)
            display.clear()
    
allumage_baby_parent()       

def mode_perdu():     # envoie un son sur le be:bi perdu
    while button_a.is_pressed():
        incomming = radio.receive()
        radio.send('music')
        if incomming:
            if incomming == 'music':
                music.play(music.BA_DING)
                sleep(5000)
                
mode_perdu()
            
