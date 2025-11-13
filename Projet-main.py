from microbit import *

import radio
radio.config(channel = 1)
radio.on()

while True:
    message = radio.receive()
    if pin_logo.is_touched():   # be:bi parent allumé
        display.show('P')
        sleep(1000)
        display.clear()
        radio.send('B')         #envoie vers le be:bi enfant
    elif message:
        display.show(message)
        sleep(1000)
        display.clear()

