from microbit import *
import radio
radio.config(channel = 1)
radio.on()
import music


def mode_perdu():     # envoie un son sur le be:bi perdu
    if button_a.was_pressed():  # envoi
        radio.send('music')
        
    incoming = radio.receive()
    if incoming == 'music':     # réception
        music.play(music.BA_DING)
                
            
def allumage_baby_parent():
    message = radio.receive()
    start = None
    if pin_logo.is_touched():   # be:bi parent allumé
        if start == None:
            start = running_time()
        elif running_time() - start >= 3000:
            display.show('P')
            sleep(2000)
            radio.send('B')
            display.clear()
            start = None
        message = radio.receive()
        
    else:
        start = None      
            
    if message:        #envoie vers le be:bi enfant
        display.show(message)
        sleep(2000)
        display.clear()
        
    return start


while True:
    mode_perdu()
    allumage_baby_parent() 
