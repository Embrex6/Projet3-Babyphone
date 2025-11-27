from microbit import *
import radio
radio.config(channel = 1)
radio.on()
import music

start_parent = None
play_music = True
quantite_lait = 0

def mode_perdu():
    global play_music

    # envoi alarme
    if button_a.was_pressed():
        radio.send('!')

    # recoit alarme
    incoming = radio.receive()
    if incoming == '!':
        if play_music:
            for i in range(6):
                music.play('c6:8')
        return

    # arret son
    if button_b.was_pressed():
        play_music = not play_music
        music.stop()

def allumage_baby_parent():
    global start_parent

    # Si on touche le logo p (parent)
    if pin_logo.is_touched():
        if start_parent is None:
            start_parent = running_time()

        # Si on garde 3 sec on devient parent
        elif running_time() - start_parent >= 3000:
            display.show('P')
            sleep(800)
            radio.send('B')   # l'autre devient enfant
            display.clear()
            start_parent = None

    else:
        start_parent = None

    # réception côté enfant
    incoming = radio.receive()
    if incoming:
        display.show(incoming)
        sleep(800)
        display.clear()

def modifie_lait():
    global quantite_lait
    
    while True:
        if retour_menu():
            return
        # ajouter une dose
        if button_a.was_pressed():
            quantite_lait += 1
            display.scroll(str(quantite_lait))

        # Retirer une dose
        if button_b.was_pressed():
            if quantite_lait > 0:
                quantite_lait -= 1
            display.scroll(str(quantite_lait))

        # Reset sur logo
        if pin_logo.is_touched():
            quantite_lait = 0
            display.scroll('0')

        sleep(50)

#Liste des modes

modes = ['MILK', 'PERDU', 'PERE']
index = 0
premier_affichage = True    

# Fonction pour revenir au menu principal

def retour_menu():
    if pin_logo.is_touched():
        start = running_time()
        while pin_logo.is_touched():
            if running_time() - start > 5000:
                display.show('M')
                sleep(500)
                return True
    return False

#boucle menu

while True:
    if premier_affichage:
        display.scroll('MENU')
        premier_affichage = False
        sleep(500)
        

    display.scroll(modes[index])

    # A = pour changer de mode

    if button_a.was_pressed():
        index = (index + 1) % len(modes)

    # B = pour sélectionner le mode

    if button_b.was_pressed():
        if modes[index] == 'MILK':
            display.scroll('MILK')
            modifie_lait()

        elif modes[index] == 'PERDU':
            display.scroll('PERDU')
            mode_perdu()

        elif modes[index] == 'PERE':
            display.scroll ('PERE')
            allumage_baby_parent()

        premier_affichage = True
    
    if retour_menu():
        premier_affichage = True
        continue

    sleep(50)


