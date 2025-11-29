from microbit import *
import radio
import random
import music

radio.config(channel=1, group=1)
radio.on()

#Initialisation des variables du micro:bit
connexion_etablie = False
cle = "motdepasse" #cle partage entre bebe et parent
cle_session = None #cle de session généré après établissement de connexion
nonce_list = set() #stocke les nonces qui pour rappelles doivent être unique à chaque fois
set_volume(100) #son max pour le microbits
role = None #variable qui va etre soit bebe ou parentNone
play_music = True #quand necessaire va dire si il faut jouer une alarme/ musique
quantite_lait = 0

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
            else : 
                car_modifier = chr((ord(car.upper()) + int_cle[cle_index] - 26) % 26 + ord('A')) #on obtient la lettre codé
            #si caractère était en minuscule, on le remet en minuscule
            if car.islower():
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

def envoie_via_TLV(cle, type, contenue):
    """
        @fonction qui permet denvoyer un message en tlv format qui est chiffrer via vigenere en mode false@
        
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

def mode_perdu():
    """
       pre: la connexion est etablie et on est dans mode perdu via menu
    
       post: si bouton A pressé, envoie un message chiffré d'alerte et lancement
             d'une alarme en boucle.
             si bouton B presse pdt l'alarme, envoie d'un message chiffre qui dit stop
             donc arret de l'alarme.
    """
    global play_music

    while True:

        if retour_menu(): #sert à sortir de la fonction en cours
            return
        # envoi alarme
        if button_a.was_pressed():
            envoie_via_TLV(cle_session, "0x02", "ALERTE")
            play_music = True
            while play_music: #boucle pour que la music soit tournee en boucle
                music.play("c6:8")
    
                # arret son
                if button_b.was_pressed():
                    envoie_via_TLV(cle_session, "0x02", "STOP")
                    play_music = False
                    music.stop()
                    break
            sleep(100)


def allumage_baby_parent():
    """
    Identifier quel est le be:bi parent et quel est le be:bi enfant à l'allumage.
    et aussi permet le lancement de l'établissement de la connexion

    pre: _

    post: si maintient pin logo pdt au moins 3s, microbits devient parent et l'autre
          devient bebe via l'envoie d'un message chiffré, reconnaissance via affichage de "P" et "B" dans microbits
          et lancement de petite musique.
    """

    global role
    if pin_logo.is_touched():
        start = running_time()
        while pin_logo.is_touched():
            if running_time() - start >= 3000: #voir si moment qu'on a commence a toucher vaut au moins 3s
                role = "parent"
                display.show("P")
                envoie_via_TLV(cle, "0x05", "ROLE:PARENT") #envoie du parent
                music.play(music.POWER_UP)
                return

    type, longueur, contenue = recevoir_message(cle)
    if type == "0x05" and contenue == "ROLE:PARENT": #bebe recoit et verifie
        role = "bebe"
        display.show("B")
        music.play(music.POWER_UP)

def modifie_lait():
    """
       pre: la connexion est etablie et on est dans mode milk via menu
       
       post: si bouton A pressé, on ajoute dose de 50 ml, on affiche et envoie chiffre
             à bebe pour que lui aussi affiche.
             si bouton B pressé, on retire dose de 10 ml, sans atteindre valeur négatif,
             on affiche et envoie chiffre à bebe pour que lui aussi affiche.
    """
    global quantite_lait
    dose_ajout = 50 #on rajoute par 50 car plus rapide et pratique pour etre en accord à la moynne de consommation de lait
    dose_retirer = 10 #on retire par 10 pour etre plus precis
    
    while True:
        if retour_menu(): #sert à sortir de la fonction en cours
            return
        # ajouter une dose
        if button_a.was_pressed():
            quantite_lait += dose_ajout
            display.scroll(str(quantite_lait) + "ml")
            envoie_via_TLV(cle_session, "0x04", str(quantite_lait)) #permet envoi au bebe par apres car lui aussi doit consulter

        # Retirer une dose
        if button_b.was_pressed():
            if quantite_lait >= dose_retirer:
                quantite_lait -= dose_retirer
            display.scroll(str(quantite_lait) + "ml")
            envoie_via_TLV(cle_session, "0x04", str(quantite_lait))
        sleep(50)

def mode_bu():
    """
       pre: connexion établie et dans mode bu via menu

       post: si bouton A pressé, affiche et envoie chiffre de la quantite de lait
             , pour que bebe affiche aussi
             si bouton B maintenu pdt 3s, met quantité de lait à 0 et envoie chiffre
             de la quantite de lait, pour que bebe affiche aussi
    """
    
    global quantite_lait

    while True:
        if retour_menu(): #sert à sortir de la fonction en cours
            return

        # a = montre la quantité de lait bu
        if button_a.was_pressed():
            display.scroll(str(quantite_lait) + "ml")
            envoie_via_TLV(cle_session, "0x04", str(quantite_lait) + "ml")

        # b = met a 0 le lait bu si maintenu 3 sec
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
    """
       pre: role déjà attribué

       post: si connexion entre bebe et parent établie, affiche connect et son positig
             , sinon affiche fail avec un son negatif
    """
    global role
    allumage_baby_parent()

    if connexion_etablie:
        display.scroll("CONNECTE")
        return
    
    if role == "parent":
        # Parent initie la demande
        reponse = etablir_connexion(cle)
        if reponse != "":
            display.scroll("Connect")
            music.play(music.POWER_UP)
        else:
            display.scroll("FAIL")
            music.play(music.POWER_DOWN)

    elif role == "bebe":
        # Bebe attend et répond
        reponse = reponse_demande_connexion(cle)
        if reponse != "":
            display.scroll("Connect")
            music.play(music.POWER_UP)
        else:
            display.scroll("FAIL")
            music.play(music.POWER_DOWN)


def detecter_etat():
    """
        pre: valeurs X et Y
        
        post: return "D" si bébé est endormi, "B" s’il est agité, "A" s’il est très agité
              basé uniquement sur les mouvements gauche/droite et avant/arrière
    """    
    x, y, _ = accelerometer.get_values() #on ignore la varible z, en rapport avec l'inclinaison car dans le cadre d'un bebe, ca fausse les résultats
    magnitude = (x**2 + y**2) ** 0.5  
    if magnitude < 300:
        return "D"   # endormi
    elif magnitude < 600:
        return "B"   # agité
    else:
        return "A"   # très agité


def mode_baby():
    """
    donc le but c'est de gerer le babyphone bebe car celui ci ne doit pas fonctionner
    de la meme manière que celui du parent, et fonctionnent comme une machine a etat via 
    lactivation ou pas du mode surveillance et la garde en memoire du dernies etat,
    ainsi il traite les messages chiffre recu par le parent et agit en conséquences.
    
       pre: role bebe et connexion etablie

       post: reagit au message recu, donc si etat on, active surveillance, si etat off, desactive 
             surveillance, aussi si recoit alerte, sonne et affiche ! et si stop, sarrete,
             aussi si type message recu cest 0x04, doit afficher la quantite de lait
    """
    
    mode_surveillance = False #donc si on active ou pas la surveillance de l'etat du bebe
    dernier_etat = None #garder en mémoire le derneir état du mode surveillance, si sur on ou off

    while connexion_etablie and role == "bebe":
        if retour_menu(): #sert à sortir de la fonction en cours
            return

        type, longueur, contenue = recevoir_message(cle_session)

        if type == "0x03":
            if contenue == "ETAT_ON" and dernier_etat != "ON": # donc si le mode de surveillance est sur off, on peut l'actuver
                envoie_via_TLV(cle_session, "0x03", "OK")
                mode_surveillance = True 
                dernier_etat = "ON"
                display.scroll("ON")

            elif contenue == "ETAT_OFF" and dernier_etat != "OFF":
                mode_surveillance = False
                dernier_etat = "OFF"
                display.scroll("OFF")

        elif type == "0x04": #but afficher la quantité de lait sur microbits bebe
            display.scroll(contenue + "ml") #ici contenue est deja un string

        elif type == "0x02" and contenue == "ALERTE": #but afficher ! et jouer une sorte d'alarme si demandée via recevoir_message
            display.show("!")

            while True:
                music.play("c6:8")
                type, longueur, contenue = recevoir_message(cle_session) #message d'arret de lalarme envoye par parent
                if type == "0x02" and contenue == "STOP":
                    display.clear()
                    music.stop()
                    break
                
        if mode_surveillance:
            etat = detecter_etat()
            envoie_via_TLV(cle_session, "0x03", etat)
            sleep(500)
                        

                
def mode_etat():
    """
    ici le but cest gerer l'etat mais cote parent, grace au bouton pour  activer ou
    desactiver le mode surveillance, la possibilite de retourner au menu aussi et recevoir
    les etat du bebe, avec possibilite de jouer un son
    
       pre: connexion etablie et le role en tant que parent

       post: recoit letat du bebe en chiffre et peut agir en consequences via des sons,
       si bouton a presse: active mode surveillance, si bouton b presse pdt 3s, mode surveillance
       desactiver
    """
    display.scroll("ETAT")
    dernier_parent_etat = None #pour garder en mémoire le dernier état recu par le parent
    
    while True:
        if retour_menu(): #sert à sortir de la fonction en cours
            return

        if button_a.was_pressed():
            envoie_via_TLV(cle_session, "0x03", "ETAT_ON") #on envoie etat on au bebe et attend confirmation
            display.scroll("ON")

            start = running_time()
            confirme = False

            while running_time() - start < 5000:
                type, longueur, contenue = recevoir_message(cle_session) #on recoit ok du bebe, donc on affiche ok, sinon, on affiche non
                if type == "0x03" and contenue == "OK":
                    confirme = True
                    break
            if confirme:
                display.scroll("OK")
            else:
                display.scroll("NON")

        if button_b.is_pressed():
            start = running_time()
            while button_b.is_pressed(): #si on appuie 3s sur b, envoie etat off, pour desactiver surveillance
                if running_time() - start >= 3000:
                    envoie_via_TLV(cle_session, "0x03", "ETAT_OFF")
                    display.scroll("OFF")
                    sleep(500)
                    break

        type, longueur, contenue = recevoir_message(cle_session)
        if type == "0x03" and contenue in ["D", "B", "A"]: #on attend et recoit les etat envouye par bebe
            display.show(contenue)

            if contenue == "A" and dernier_parent_etat != "A":
                for i in range(5): #garder le son un peu longtemps
                    music.play(['C5:4'], wait=False)
            dernier_parent_etat = contenue #contenue cest string, ainsi dernier parent etat est mis a jour

        sleep(100)
            

#Liste des modes

modes = ['MILK', 'PERDU', 'BU' , 'ETAT']
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


while True:

    if not connexion_etablie:
        protocole_connexion_roles() #donc va lancer connexion une fois que parent determines via 3s touche pin logo
        sleep(100)
        continue  # on attend que la connexion soit faite

    if role == "parent":
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
        