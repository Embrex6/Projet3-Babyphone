from microbit import *
import radio
import random
import music

radio.config(channel=1, group=1)
radio.on()

connexion_etablie = False
cle = "motdepasse"
cle_session = None
nonce_list = set()
set_volume(100)
role = None
quantite_lait = 0

def hashing(string):
    def to_32(value):
        value = value % (2 ** 32)
        if value >= 2**31:
            value = value - 2 ** 32
        value = int(value)
        return value
    if string:
        x = ord(string[0]) << 7
        m = 1000003
        for c in string:
            x = to_32((x*m) ^ ord(c))
        x ^= len(string)
        if x == -1:
            x = -2
        return str(x)
    return ""

def vigenere(message, cle, dechiffrement=False):
    texte = ""
    longueur_cle = len(cle)
    int_cle = [ord(k) for k in cle]
    for i, car in enumerate(str(message)):
        cle_index = i % longueur_cle
        if car.isalpha():
            if dechiffrement:
                car_modifier = chr((ord(car.upper()) - int_cle[cle_index] + 26) % 26 + ord('A'))
            else:
                car_modifier = chr((ord(car.upper()) + int_cle[cle_index] - 26) % 26 + ord('A'))
            if car.islower():
                car_modifier = car_modifier.lower()
            texte += car_modifier
        elif car.isdigit():
            if dechiffrement:
                car_modifier = str((int(car) - int_cle[cle_index]) % 10)
            else:
                car_modifier = str((int(car) + int_cle[cle_index]) % 10)
            texte += car_modifier
        else:
            texte += car
    return texte

def envoie_via_TLV(cle, type, contenue):
    message_tlv = type + "|" + str(len(contenue)) + "|" + contenue
    message_tlv_chiffre = vigenere(message_tlv, cle, dechiffrement=False)
    radio.send(message_tlv_chiffre)

def deballage(message_tlv_chiffre, cle):
    try:
        dechiffrement = vigenere(message_tlv_chiffre, cle, dechiffrement=True)
        type, longueur, contenue = dechiffrement.split("|")
        longueur = int(longueur)
        if longueur != len(contenue):
            return "", 0, ""
        return type, longueur, contenue
    except:
        return "", 0, ""

def recevoir_message(cle):
    message_recu = radio.receive()
    if not message_recu:
        return "", 0, ""
    type, longueur, contenue = deballage(message_recu, cle)
    if type == "" or longueur == 0 or contenue == "":
        return "", 0, ""
    return type, longueur, contenue

def calcul_reponse_challenge(challenge):
    return hashing(challenge)

def etablir_connexion(cle):
    global cle_session, connexion_etablie
    try:
        challenge = str(random.randint(1000, 9999))
        new_nonce = str(random.randint(100, 999))
        contenue = new_nonce + ":" + challenge
        envoie_via_TLV(cle, "0x01", contenue)
        time_max = running_time() + 5000
        while running_time() < time_max:
            type, longueur, contenue = recevoir_message(cle)
            if contenue != "" and type == "0x01":
                nonce, reponse = contenue.split(":")
                if reponse == hashing(challenge):
                    cle_session = cle + hashing(challenge)
                    connexion_etablie = True
                    return reponse
            sleep(100)
        return ""
    except:
        return ""

def reponse_demande_connexion(cle):
    global cle_session, connexion_etablie
    try:
        type, longueur, contenue = recevoir_message(cle)
        if type == "0x01" and contenue != "":
            nonce, challenge = contenue.split(":")
            if nonce in nonce_list:
                return ""
            nonce_list.add(nonce)
            reponse = hashing(challenge)
            new_nonce = str(random.randint(100, 999))
            contenue_final = new_nonce + ":" + reponse
            envoie_via_TLV(cle, "0x01", contenue_final)
            nonce_list.add(new_nonce)
            cle_session = cle + reponse
            connexion_etablie = True
            return reponse
        else:
            return ""
    except:
        return ""

def mode_perdu():
    global play_music
    while True:
        if retour_menu():
            return
        if button_a.was_pressed():
            envoie_via_TLV(cle_session, "0x02", "ALERTE")
            play_music = True
            while play_music:
                music.play("c6:8")
                if button_b.was_pressed():
                    envoie_via_TLV(cle_session, "0x02", "STOP")
                    play_music = False
                    music.stop()
                    break
            sleep(100)

def allumage_baby_parent():
    global role
    if pin_logo.is_touched():
        start = running_time()
        while pin_logo.is_touched():
            if running_time() - start >= 3000:
                role = "parent"
                display.show("P")
                envoie_via_TLV(cle, "0x05", "ROLE:PARENT")
                music.play(['C5:4'])
                return
    type, longueur, contenue = recevoir_message(cle)
    if type == "0x05" and contenue == "ROLE:PARENT":
        role = "bebe"
        display.show("B")
        music.play(['C5:4'])

def modifie_lait():
    global quantite_lait
    dose_ajout = 50
    dose_retirer = 10
    while True:
        if retour_menu():
            return
        if button_a.was_pressed():
            quantite_lait += dose_ajout
            display.scroll(str(quantite_lait) + "ml")
            envoie_via_TLV(cle_session, "0x04", str(quantite_lait))
        if button_b.was_pressed():
            if quantite_lait >= dose_retirer:
                quantite_lait -= dose_retirer
            display.scroll(str(quantite_lait) + "ml")
            envoie_via_TLV(cle_session, "0x04", str(quantite_lait))
        sleep(50)

def mode_bu():
    global quantite_lait
    while True:
        if retour_menu():
            return
        if button_a.was_pressed():
            display.scroll(str(quantite_lait) + "ml")
            envoie_via_TLV(cle_session, "0x04", str(quantite_lait) + "ml")
        if button_b.is_pressed():
            start = running_time()
            while button_b.is_pressed():
                if running_time() - start >= 3000:
                    quantite_lait = 0
                    display.scroll("0ml")
                    envoie_via_TLV(cle_session, "0x04", "0ml")
                    sleep(500)
                    break
        sleep(50)


def protocole_connexion_roles():
    global role
    allumage_baby_parent()
    if connexion_etablie:
        display.scroll("OK")
        return
    if role == "parent":
        reponse = etablir_connexion(cle)
        if reponse != "":
            display.scroll("OK")
            music.play(['C5:4'])
        else:
            display.scroll("NO")
            music.play(['C4:4'])
    elif role == "bebe":
        reponse = reponse_demande_connexion(cle)
        if reponse != "":
            display.scroll("OK")
            music.play(['C5:4'])
        else:
            display.scroll("NO")
            music.play(['C4:4'])

def detecter_etat():
    x, y, _ = accelerometer.get_values()
    magnitude = (x**2 + y**2) ** 0.5
    if magnitude < 300:
        return "D"
    elif magnitude < 600:
        return "B"
    else:
        return "A"

def mode_baby():
    mode_surveillance = False
    dernier_etat = None
    while connexion_etablie and role == "bebe":
        if retour_menu():
            return
        type, longueur, contenue = recevoir_message(cle_session)
        if type == "0x03":
            if contenue == "ETAT_ON" and dernier_etat != "ON":
                envoie_via_TLV(cle_session, "0x03", "OK")
                mode_surveillance = True
                dernier_etat = "ON"
                display.scroll("ON")
            elif contenue == "ETAT_OFF" and dernier_etat != "OFF":
                mode_surveillance = False
                dernier_etat = "OFF"
                display.scroll("OFF")
        elif type == "0x04":
            display.scroll(contenue + "ml")
        elif type == "0x02" and contenue == "ALERTE":
            display.show("!")
            while True:
                music.play("c6:8")
                type, longueur, contenue = recevoir_message(cle_session)
                if type == "0x02" and contenue == "STOP":
                    display.clear()
                    music.stop()
                    break

        if mode_surveillance:
            etat = detecter_etat()
            envoie_via_TLV(cle_session, "0x03", etat)
            sleep(500)

def mode_etat():
    display.scroll("ETAT")
    dernier_parent_etat = None
    while True:
        if retour_menu():
            return
        if button_a.was_pressed():
            envoie_via_TLV(cle_session, "0x03", "ETAT_ON")
            display.scroll("ON")
            start = running_time()
            confirme = False
            while running_time() - start < 5000:
                type, longueur, contenue = recevoir_message(cle_session)
                if type == "0x03" and contenue == "OK":
                    confirme = True
                    break
            if confirme:
                display.scroll("OK")
            else:
                display.scroll("NON")
        if button_b.is_pressed():
            start = running_time()
            while button_b.is_pressed():
                if running_time() - start >= 3000:
                    envoie_via_TLV(cle_session, "0x03", "ETAT_OFF")
                    display.scroll("OFF")
                    sleep(500)
                    break
        type, longueur, contenue = recevoir_message(cle_session)
        if type == "0x03" and contenue in ["D", "B", "A"]:
            display.show(contenue)
            if contenue == "A" and dernier_parent_etat != "A":
                for i in range(6):
                    music.play(['C5:4'], wait=False)
            dernier_parent_etat = contenue
        sleep(100)

modes = ['MILK', 'PERDU', 'BU', 'ETAT']
index = 0
premier_affichage = True

def retour_menu():
    if pin_logo.is_touched():
        start = running_time()
        while pin_logo.is_touched():
            if running_time() - start > 5000:
                display.show('M')
                sleep(500)
                return True
    return False

while True:
    if not connexion_etablie:
        protocole_connexion_roles()
        sleep(100)
        continue
    if role == "parent":
        if premier_affichage:
            display.scroll('MENU')
            premier_affichage = False
            sleep(500)
        display.scroll(modes[index])
        if button_a.was_pressed():
            index = (index + 1) % len(modes)
        if button_b.was_pressed():
            if modes[index] == 'MILK':
                display.scroll('MILK')
                modifie_lait()
            elif modes[index] == 'PERDU':
                display.scroll('PERDU')
                mode_perdu()
            elif modes[index] == 'BU':
                display.scroll('BU')
                mode_bu()
            elif modes[index] == 'ETAT':
                display.scroll('ETAT')
                mode_etat()
            premier_affichage = True
        if retour_menu():
            premier_affichage = True
            continue
        sleep(50)
    elif role == "bebe":
        mode_baby()

