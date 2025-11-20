from microbit import *
import radio
radio.config(channel = 1)
radio.on()
import music

def mode_perdu():   
    """
    Emettre un son sur un be:bi depuis l'autre si le premier est perdu.
    """
    play_music = True
    if button_a.is_pressed():  # envoi
        radio.send('!')
        
    incoming = radio.receive()
    if incoming == '!':     # réception
        if play_music == True:
            for i in range(10):
                music.play('c6: 8')  #son aigu
        elif button_b.was_pressed():  # arrêter le son
            music.stop()
                                   
def allumage_baby_parent():
    """
    Identifier quel est le be:bi parent et quel est le be:bi enfant à l'allumage.
    """
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

quantite_lait = 0   # quantité totale de doses consommées
def modifie_lait(): 
    """
    Quantité de lait que le bébé a bu. 
    """
    global quantite_lait  
    if button_a.was_pressed():    # ajouter une dose
        quantite_lait += 1
        display.scroll(str(quantite_lait))
        
    if button_b.was_pressed():
        if quantite_lait > 0:     # enlever une dose
            quantite_lait -= 1
            display.scroll(str(quantite_lait))
            
    if pin_logo.is_touched(): # reset
        quantite_lait = 0
        display.scroll(str(quantite_lait))


while True:      # faire l'interface utilisateur, pas encore fonctionnel
    allumage_baby_parent()
    if pin0.is_touched():
        display.scroll('Milk')
        modifie_lait()
    if pin1.is_touched():
        display.scroll('! ! !')
        mode_perdu()
