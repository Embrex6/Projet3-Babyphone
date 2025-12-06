#################################################################################################################
#                                                                                                               # 
###!!! Ce code N'EST PAS la version à éxécuter puisque avec docstring, donc sature la mémoire du microbits !!!###
#                       Veuillez donc exécuter l'autre version identique mais sans docstring                    #                                                                                         
#################################################################################################################
#Le code a été surcommenté pour permettre de ne pas perdre le fil, lors de la longue lecture du code

### IMPORTATION ###
from microbit import *
import radio
import random
import music

### REGLAGE MICROBITS ###
radio.config(channel=1, group=1)
radio.on()
set_volume(100)

### Initialisation des variables du micro:bit ###
connexion_etablie = False 
cle = "motdepasse" #cle partage entre bebe et parent
cle_session = None #cle de session généré après établissement de connexion
nonce_list = set() #stocke les nonces qui pour rappelles doivent être unique à chaque fois
role = None #variable qui va etre soit bebe ou parent ou None
quantite_lait = 0 #affichage lait, gérer depuis parent
quantite_lait_bebe = 0 #affichage lait stocker pour utilisation avec microbits bebe
x0, y0, z0 = accelerometer.get_values() #variable initiale pour ensuite faire la différence

### FONCTIONS DE CRYPTAGES ###
def hashing(string):
    """
       pre: string est une chaine de caractère
       post: return la chaine de caractère haché
    """
    def to_32(value):
        """
        Fonction interne utilisée par hashing.
        Convertit une valeur en un entier signé de 32 bits.
        Si 'value' est un entier plus grand que 2 ** 31, il sera tronqué.

        :param (int) value: valeur du caractère transformé par la valeur de hachage de cette itération
        :return (int): entier signé de 32 bits représentant 'value'
        """
        value = value % (2 ** 32)
        if value >= 2**31:
            value = value - 2 ** 32
        value = int(value)
        return value
    if string:
        x = ord(string[0]) << 7 #ord transforme lettre en valeur int() et << 7 equivaut à un decalage de bit en faisont "...*2**7"
        m = 1000003
        for c in string:
            x = to_32((x*m) ^ ord(c))
        x ^= len(string)
        if x == -1:
            x = -2
        return str(x)
    return ""

def vigenere(message, cle, dechiffrement=False):
    """
       pre : message c'est chaine de caractère, clé c'est aussi chaine de caractere, dechiffrement est
             un booléen, true pour mode dechiffrement et false pour mode chiffrement
       post : return une chaine de caractere qui correpond au message chiffre ou dechiffré au besoin
    """
    texte = ""
    longueur_cle = len(cle)
    int_cle = [ord(k) for k in cle] #chaque caractère de notre clé sera transformé en int
    for i, car in enumerate(str(message)): #renvoie tupple de (indice, caractère)
        cle_index = i % longueur_cle
        #chiffrement/dechiffrement : lettres
        if car.isalpha():
            if dechiffrement:
                car_modifier = chr((ord(car.upper()) - int_cle[cle_index] + 26) % 26 + ord('A')) #on obtient la lettre originale
            else:
                car_modifier = chr((ord(car.upper()) + int_cle[cle_index] - 26) % 26 + ord('A')) #on obtient la lettre codé
            if car.islower(): #si caractère était en minuscule, on le remet en minuscule
                car_modifier = car_modifier.lower()
            texte += car_modifier
        #chiffrement/dechiffrement : chiffres
        elif car.isdigit(): #digit veut dire chiffre
            if dechiffrement:
                car_modifier = str((int(car) - int_cle[cle_index]) % 10) #on obtien le chiffre originale
            else:
                car_modifier = str((int(car) + int_cle[cle_index]) % 10) #on obtient le chiffre codé
            texte += car_modifier
        else:
            texte += car
    return texte #notre texte chiffre ou déchiffre au besoin

### LES FONCTIONS POUR GERER LE FORMAT TLV ###
def envoie_via_TLV(cle, type, contenue):
    """
        fonction qui permet denvoyer un message en tlv format qui est chiffrer via vigenere en mode false
        
        pre: cle est chaine de caractere, type aussi, et contenue aussi
        post: ne retourne rien va envoyer via radio.send y a pas besoin de return quoique ce soit
    """
    message_tlv = type + "|" + str(len(contenue)) + "|" + contenue
    message_tlv_chiffre = vigenere(message_tlv, cle, dechiffrement=False)
    radio.send(message_tlv_chiffre)

def deballage(message_tlv_chiffre, cle):
    """
        Déballe et déchiffre les messages tlv chiffré reçus via l'interface radio du micro:bit
        Cette fonction renvoit les différents champs du message passé en paramètre pour que ca soit utilisable pour notre programme
        
        pre: message_tlv_chiffre et cle sont des chaines de caractères
        post: return le type en chaine de caractère, la longeur en int et le contenue en chaine de caractère
    """
    try:
        dechiffrement = vigenere(message_tlv_chiffre, cle, dechiffrement=True)
        type, longueur, contenue = dechiffrement.split("|")
        longueur = int(longueur)
        if longueur != len(contenue):
            return "", 0, ""
        return type, longueur, contenue
    except:
        return "", 0, ""
    
#vérifie le message recu et si nécessaire, utilise la fct déballage
def recevoir_message(cle):
    """
        Traite les messages reçus via l'interface radio du micro:bit
        Cette fonction utilise la fonction deballage pour renvoyer les différents champs du message passé en paramètre utilisable par notre programme
        Si une erreur survient, les 3 champs sont retournés vides

        pre: cle est chaine de caractère
        post: return le type en chaine de caractère, la longeur en int et le contenue en chaine de caractère
    """
    message_recu = radio.receive()
    if not message_recu:
        return "", 0, ""
    type, longueur, contenue = deballage(message_recu, cle)
    if type == "" or longueur == 0 or contenue == "":
        return "", 0, ""
    return type, longueur, contenue

### FONCTIONS POUR GERER L'ETABLISSEMENT DE CONNEXION ###
def calcul_reponse_challenge(challenge):
    """
        Calcule la réponse au challenge initial de connection avec l'autre micro:bit

        pre: challenge est chaine de caractère
        post: return une chaine de caractère qui correpond a une reponse du challenge via notre fonction hashing
    """
    return hashing(challenge)

def etablir_connexion(cle):
    """
        Etablissement de la connexion avec l'autre micro:bit
        Si il y a une erreur, la valeur de retour est vide
        
        pre: cle est chaine de caractère
        post: return en chaine de caractère la reponse au challenge via la fct: calcul_reponse_challenge
    """
    global cle_session, connexion_etablie
    try:
        challenge = str(random.randint(1000, 9999))
        new_nonce = str(random.randint(100, 999))
        contenue = new_nonce + ":" + challenge
        envoie_via_TLV(cle, "0x01", contenue)
        time_max = running_time() + 5000 # on patiente 5s grand max (car ca peut prendre du temps)
        while running_time() < time_max:
            type, longueur, contenue = recevoir_message(cle)
            if contenue != "" and type == "0x01":
                nonce, reponse = contenue.split(":")
                if reponse == hashing(challenge): #donc si la réponse que on a recu correspond a notre reponse, on peut creer une nouvelle clé
                    cle_session = cle + hashing(challenge)
                    connexion_etablie = True
                    return reponse
            sleep(100)
        return ""
    except:
        return ""

#on répond à la demande de connexion en utilisant la fct calcul reponse challenge
def reponse_demande_connexion(cle):
    """
        Réponse au challenge initial de connection avec l'autre micro:bit
        Si il y a une erreur, la valeur de retour est vide
        
        pre: cle est une chaine de caractere
        post: return une chaine de caractère qui correpond à la reponse au challenge via calcul reponse challenge
    """
    global cle_session, connexion_etablie #global permet accés à une variable extérieur
    try:
        type, longueur, contenue = recevoir_message(cle)
        if type == "0x01" and contenue != "":
            nonce, challenge = contenue.split(":")
            if nonce in nonce_list: #ainsi on évite les attaques par rejeu
                return ""
            nonce_list.add(nonce)
            reponse = hashing(challenge) #on repond au challenge, pour ca faut une bonne reponse, donc via hashing
            new_nonce = str(random.randint(100, 999)) #génération de notre nouveau nonce unique
            contenue_final = new_nonce + ":" + reponse
            envoie_via_TLV(cle, "0x01", contenue_final) #voila on repond, donc bien un nouveau nonce et la reponse
            nonce_list.add(new_nonce)
            cle_session = cle + reponse #donc notre nouvelle clé
            connexion_etablie = True
            return reponse
        else:
            return ""
    except:
        return ""
    
### FONCTIONS POUR GERER L'ETABLISSEMENT DES ROLES ET LA CONNEXION ###
def allumage_baby_parent():
    """
    Identifier quel est le be:bi parent et quel est le be:bi enfant à l'allumage.
    et aussi permet le lancement de l'établissement de la connexion

    pre: _
    post: si maintient pin logo pdt au moins 3s, microbits devient parent et l'autre
          devient bebe via l'envoie d'un message chiffré, reconnaissance via affichage de "P" et "B"
    """
    global role
    if pin_logo.is_touched():
        start = running_time()
        while pin_logo.is_touched():
            if running_time() - start >= 3000: #voir si moment qu'on a commence a toucher vaut au moins 3s
                role = "parent"
                display.show("P")
                envoie_via_TLV(cle, "0x05", "ROLE:PARENT") #envoie du parent
                music.play(['C5:4'])
                return
    type, longueur, contenue = recevoir_message(cle)
    if type == "0x05" and contenue == "ROLE:PARENT": #bebe recoit et verifie
        role = "bebe"
        display.show("B")
        music.play(['C5:4'])
        
def protocole_connexion_roles():
    """
       pre: role déjà attribué
       post: si connexion entre bebe et parent établie, affiche connect et son positif
             , sinon affiche fail avec un son negatif
    """
    global role
    allumage_baby_parent()
    if connexion_etablie:
        display.scroll("OK")
        return
    if role == "parent": # Parent initie la demande
        reponse = etablir_connexion(cle)
        if reponse != "":
            display.scroll("OK")
            music.play(['C5:4'])
        else:
            display.scroll("NO")
            music.play(['C4:4'])
    elif role == "bebe": # Bebe attend et répond
        reponse = reponse_demande_connexion(cle)
        if reponse != "":
            display.scroll("OK")
            music.play(['C5:4'])
        else:
            display.scroll("NO")
            music.play(['C4:4'])
        
### FONCTIONS CORRESPONDANT AUX DIFFERENTS MODES ###
def mode_perdu():
    """
       pre: la connexion est etablie et on est dans mode perdu via menu
       post: si bouton A pressé, envoie un message chiffré d'alerte 
             si bouton B presse, envoie d'un message chiffre qui dit stop.
    """
    global play_music
    while True:
        if retour_menu(): #sert à sortir de la fonction en cours
            return
        if button_a.was_pressed(): # envoi alarme pour prevenir bebe de faire son
            envoie_via_TLV(cle_session, "0x02", "ALERTE")
            display.show("!")
            play_music = True
            while play_music: #si musique est jouer et que on appui sur b, envoie stop pour arreter son chez bebe
                if button_b.was_pressed():
                    envoie_via_TLV(cle_session, "0x02", "STOP")
                    display.clear()
                    play_music = False
                    music.stop()
                    break
            sleep(100)

def modifie_lait():
    """
       pre: la connexion est etablie et on est dans mode milk via menu     
       post: si bouton A pressé, on ajoute dose de 50 ml, on affiche et envoie chiffre.
             si bouton B pressé, on retire dose de 10 ml, sans atteindre valeur négatif,
             on affiche et envoie chiffre.
    """
    global quantite_lait
    dose_ajout = 50 #on rajoute par 50 car plus rapide et pratique pour etre en accord à la moynne de consommation de lait
    dose_retirer = 10 #on retire par 10 pour etre plus precis
    while True:
        if retour_menu(): #sert à sortir de la fonction en cours
            return
        if button_a.was_pressed(): # ajouter une dose
            quantite_lait += dose_ajout
            display.scroll(str(quantite_lait) + "ml")
            envoie_via_TLV(cle_session, "0x04", str(quantite_lait)) #permet envoi au bebe par apres car lui aussi doit consulter
        if button_b.was_pressed(): # Retirer une dose
            if quantite_lait >= dose_retirer:
                quantite_lait -= dose_retirer
            display.scroll(str(quantite_lait) + "ml")
            envoie_via_TLV(cle_session, "0x04", str(quantite_lait)) #permet envoi au bebe par apres car lui aussi doit consulter
        sleep(50)

def mode_bu():
    """
       pre: connexion établie et dans mode bu via menu
       post: si bouton A pressé, affiche et envoie chiffre de la quantite de lait
             si bouton B maintenu pdt 3s, met quantité de lait à 0 et envoie chiffre
    """
    global quantite_lait
    while True:
        if retour_menu(): #sert à sortir de la fonction en cours
            return
        if button_a.was_pressed(): # a = montre la quantité de lait bu
            display.scroll(str(quantite_lait) + "ml")
            envoie_via_TLV(cle_session, "0x04", str(quantite_lait))
        if button_b.is_pressed(): # b = met a 0 le lait bu si maintenu 3 sec
            start = running_time()
            while button_b.is_pressed():
                if running_time() - start >= 3000:
                    quantite_lait = 0
                    display.scroll("0ml")
                    envoie_via_TLV(cle_session, "0x04", "0")
                    sleep(500)
                    break
        sleep(50)

### UTILLISATION ACCELEROMETRE ###
def detecter_etat():
    """
        pre: valeurs X et Y et Z
        post: return "D" si bébé est endormi, "B" s’il est agité, "A" s’il est très agité
    """   
    global x0, y0, z0
    x, y, z = accelerometer.get_values()
    dx = abs(x - x0) #différence x actuelle et x avant, comme ca mouvement net
    dy = abs(y - y0)
    dz = abs(z - z0)
    x0, y0, z0 = x, y, z #ancienne valeur mis à joue à chaque fois
    magnitude = (dx**2 + dy**2 + dz**2) ** 0.5 #formule pour l'intensité du mouvement
    if magnitude < 450:
        return "D" # état détente
    elif magnitude < 1200:
        return "B" # état bouge un peu
    else:
        return "A" # état agité
    
### GESTION ETAT COTE BEBE ET AFFICHAGE LAIT ###
def mode_baby():
    """
       traite les messages chiffre recu par le parent et agit en conséquences.
    
       pre: role bebe et connexion etablie
       post: reagit au message recu et envoie si necessaire, et si buton A presse, affiche quantite lait
    """
    global quantite_lait_bebe
    mode_surveillance = False #activer ou désactiver la surveillance des état du bébé
    dernier_etat = None #pour garder en mémoire si le mode de surveillance est sur on ou off
    start_berceuse = None #garder en mémoire quand la berceuse a commencé avec running time
    berceuse_active = False #pour dire si la berceuse est active ou pas
    dernier_etat_envoye = None
    
    while connexion_etablie and role == "bebe":

        if button_a.was_pressed():
            display.scroll(str(quantite_lait_bebe) + "ml") # afficher lait chez bebe avec buton A

        type, longueur, contenue = recevoir_message(cle_session)
        if type == "0x03":
            if contenue == "ETAT_ON" and dernier_etat != "ON": #on active donc la surveillance
                envoie_via_TLV(cle_session, "0x03", "OK")
                mode_surveillance = True
                dernier_etat = "ON"
                display.scroll("ON")
            elif contenue == "ETAT_OFF" and dernier_etat != "OFF": #on désactive donc la surveillance
                mode_surveillance = False
                dernier_etat = "OFF"
                display.scroll("OFF")
                
        elif type == "0x04":
            quantite_lait_bebe = contenue
            display.scroll(contenue + "ml") #chaque changement de quantite de lait chez parent, est mis à jour chez bebe
            
        elif type == "0x02" and contenue == "ALERTE":
            display.show("!")
            while True: #donc quand le parent demande, bebe fait alarme
                music.play("c6:8")
                type, longueur, contenue = recevoir_message(cle_session)
                if type == "0x02" and contenue == "STOP":
                    display.clear()
                    music.stop() #donc quand parent demande stop, la musique s'arrête
                    break #pour sortir de la boucle immédiatement

        elif type == "0x07":
            if contenue == "URGENCE": 
                display.show("!") #ca affiche quand le bebe est très agité
            elif contenue == "STOP_URGENCE":
                display.clear() #ca retire l'affichage une fois changement d'état

        elif type == "0x06" and contenue == "BERCEUSE":
            display.show(Image.HEART) #a chaque fois que le bebe bouge un peu, donc a chaque etat B, ya petit coeur
            start_berceuse = running_time()
            berceuse_active = True
            music.play(["C4:4", "D4:4", "E4:4", "C4:4", "E4:4", "F4:4", "G4:8"], wait=False, loop=True)
            #donc quand ya wait false, cest pour eviter dattendre la fin de la melodie si la boucle doit etre relance
            #et loop = true cest pour boucler
                
        elif type == "0x06" and contenue == "STOP_MUSIC": #on recoit stop dans le contexte dun etat D ou A
            if berceuse_active and start_berceuse is not None:
                if running_time() - start_berceuse >= 5000: #si berceuse active depuis au moins 5s, on peut eteindre
                    display.clear()
                    music.stop()
                    berceuse_active = False

        elif mode_surveillance:
            etat = detecter_etat() #donc A, D ou B
            if etat != dernier_etat_envoye: #ainsi on évite des envoie répétitive du même état
                envoie_via_TLV(cle_session, "0x03", etat)
                dernier_etat_envoye = etat
            if berceuse_active and start_berceuse is not None:
                if etat in ["D","A"]: #contrairement au bloc au dessus, ici ca peut sarreter sans dependre dun message, stop music, securite ++ pour eviter boucle
                    if running_time() - start_berceuse >= 5000:
                        display.clear()
                        music.stop()
                        berceuse_active = False

            sleep(500)
            
### GESTION ETAT COTE PARENT ###
def mode_etat():
    """
       pre: connexion etablie et le role en tant que parent
       post: recoit letat du bebe en chiffre et peut agir en consequences via des sons et envoie chiffre,
       si bouton a presse: active mode surveillance, si bouton b presse pdt 3s, mode surveillance
       desactiver
    """
    etat_actuelle = None
    alerte_active_parent = False #pour dire si alarme lancé ou pas
    alerte_start = 0 #sorte de chrono
    
    while True:
        if retour_menu(): #pour sortir de la fonction en cours
            return
        if button_a.was_pressed():
            envoie_via_TLV(cle_session, "0x03", "ETAT_ON")
            display.scroll("ON")
            start = running_time()
            confirme = False
            while running_time() - start < 5000: #le laps de temps ne doit pas surpasser les 5s pour la durre denvoie dactivation du mode surveillance
                type, longueur, contenue = recevoir_message(cle_session)
                if type == "0x03" and contenue == "OK":
                    confirme = True
                    break #pour completement sortir de la boucle, une fois condition validé
            if confirme:
                display.scroll("OK")
            else:
                display.scroll("NON") #on nas pas pu faire le lien entre parent et bebe pour le paratge des états, faut recommencer
        if button_b.is_pressed():
            start = running_time()
            while button_b.is_pressed():
                if running_time() - start >= 3000:
                    envoie_via_TLV(cle_session, "0x03", "ETAT_OFF")
                    display.scroll("OFF") #si b appuyés pdt 3s, on desactive le mode de surveillance
                    sleep(500)
                    break
                    
        type, longueur, contenue = recevoir_message(cle_session)
        if type == "0x03" and contenue in ["D", "B", "A"]: #on attend et recoit les etat envouye par bebe
            display.show(contenue)
            etat_actuelle = contenue

            if etat_actuelle == "A":
                if not alerte_active_parent: #donc si alarme pas encore lance et A, ca va lance
                    alerte_active_parent = True #pour dire que alarme est lancé
                    alerte_start = 0 #comme ca a chaque fois que etat A, le soi disant chrono est mis à zero
                    music.play(["C6:4"], wait=False, loop=True)
                    envoie_via_TLV(cle_session, "0x07", "URGENCE")

            elif etat_actuelle == "B":
                envoie_via_TLV(cle_session, "0x07", "STOP_URGENCE")
                envoie_via_TLV(cle_session, "0x06", "BERCEUSE")
                if alerte_active_parent and alerte_start == 0:
                    alerte_start = running_time() #puisque autre etat que A, maintenat le chrono est compté(doit pas depasser 5s)
    
            elif etat_actuelle == "D":
                envoie_via_TLV(cle_session, "0x06", "STOP_MUSIC")
                envoie_via_TLV(cle_session, "0x07", "STOP_URGENCE")
                if alerte_active_parent and alerte_start == 0:
                    alerte_start = running_time()

        if alerte_active_parent and alerte_start > 0:
            if running_time() - alerte_start >= 5000: #si etat autre que A, doit pas depasser 5s dalarme
                music.stop()
                display.clear()
                alerte_active_parent = False
                alerte_start = 0
                if etat_actuelle:
                    display.show(etat_actuelle)

        sleep(100)

### FONCTION MENU ET LANCEMENT DES FONCTIONS ###
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
     
                
        


