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
    type, longueur, contenu = deballage(message_recu, cle)
    if type == "" or longueur == 0 or contenu == "":
        return "", 0, ""
    return type, longueur, contenu


def calcul_reponse_challenge(challenge):
    """
        Calcule la réponse au challenge initial de connection avec l'autre micro:bit

        pre: challenge est chaine de caractère
        
        post: return une chaine de caractère qui correpond a une reponse du challenge via notre fonction hashing
    """
    return hashing(challenge)



#on répond à la demande de connexion en utilisant la fct calcul reponse challenge
def reponse_demande_connexion(cle):
    """
        Réponse au challenge initial de connection avec l'autre micro:bit
        Si il y a une erreur, la valeur de retour est vide
        
        pre: cle est une chaine de caractere
        
        post: return une chaine de caractère qui correpond à la reponse au challenge via calcul reponse challenge
    """
    try:
        global cle_session, connexion_etablie #global permet accés à une variable extérieur
        
        type, longueur, contenue = recevoir_message(cle)
        if type == "0x01" and contenue != "":
            nonce, challenge = contenue.split(":")
            if nonce in nonce_list: #ainsi on évite les attaques par rejeu
                return ""
            nonce_list.add(nonce)
            
            reponse = calcul_reponse_challenge(contenue)
            new_nonce = str(random.randint(100, 999)) #génération de notre nouveau nonce unique
            contenue_final = new_nonce + ":" + reponse
            envoie_via_TLV(cle, "0x01", contenue_final)
            nonce_list.add(new_nonce)
            

            cle_session = cle + reponse #donc notre nouvelle clé
            connexion_etablie = True
            return reponse
        else:
            return ""
        
    except:
        return ""

def allumage_baby_parent():
    """
    Identifier quel est le be:bi parent et quel est le be:bi enfant à l'allumage.
    et aussi permet le lancement de l'établissement de la connexion
    """
    message = radio.receive()
    role = None
    start = running_time()
    while pin_logo.is_touched(): 
        if running_time() - start >= 3000:
            role = "parent"
            display.show('P')
            sleep(2000)
            radio.send('0x01:ETABLISSEMENT_CONNEXION')
            display.clear()
            break
        message = radio.receive()     
            
    if message == "0x01:ETABLISSEMENT_CONNEXION": #envoie vers le be:bi enfant
        role = "bebe"
        display.show('B')
        sleep(2000)
        radio.send('0x01:ETABLISSEMENT_CONNEXION')
        display.clear()

    return role



def main():
    """Notre main, c'est notre tableau de commande pour tout gérer, en plusieurs étapes:
       n°1, on va allumer nos microbits et faire établissement de connexion (on pourra aussi les éteindre)
       n°2, vérifier justement si il y a bien une connexion établie, donc visible via display scroll("voir microbits")
       n°3 une boucle while qui une fois la connexion établie, nos différente fonction peuvent potentiellement être enclenché
    """
    global cle_session, connexion_etablie #global pour avoir accès à des variables ectérieur
    connexion_etablie = False #initialement false
    interrupteur = False #on definit mode off et on pour notre microbits, si sur false, cest a dire en "mode eteint"
    
    while True:
        if not interrupteur and pin_logo.is_touched():
            start = running_time()
            while pin_logo.is_touched():
                if running_time() - start >= 3000:
                    Interrupteur = True #donc cest mode allumer
                    display.show("ON")
                    break
            #donc ici cest une securite si apres un apppuie de pin logo, aucun role na etait attribue, ca permet deviter une erreur et de ressayer
            role = None
            while role is None:
                role = allumage_baby_parent()
 
            try:
                if role == "parent":
                    reponse = reponse_demande_connexion(cle)
                    if reponse == "" or not connexion_etablie:
                        display.scroll("Erreur connexion")
                        interrupteur = False
                        continue
                    display.scroll("Connexion Etablie")

                elif role == "bebe":
                    reponse = etablir_connexion(cle)
                    if reponse == "":
                        display.scroll("Erreur connexion")
                        interrupteur = False
                        continue
                    connexion_etablie = True
                    display.scroll("Connexion Etablie")

            except:
                display.scroll("Erreur connexion")
                interrupteur = False
                connexion_etablie = False
                continue
    
        elif interrupteur and pin_logo.is_touched(): #donc si on mode allumer et on maintient appuyer, CA VA ETEINDRE
            start = running_time()
            while pin_logo.is_touched():
                if running_time() - start >= 3000:
                    interrupteur = False
                    connexion_etablie = False
                    display.show("OFF")
                    break
        
        
    if connexion_etablie and interrupteur:
        try:
            type, longueur, contenue = recevoir_message(cle_session) #c'est à partir de ce moment que la clé est remplacé par notre clé de session
            if contenue == "":
                continue #pour tout message vide, on ignore est continue l'itération
            nonce, message = contenue.split(":")
            if nonce in nonce_list:
                continue
            else:
                nonce_list.add(nonce)
                
                ############################################################################
                ##  !!!ICI ON MET LES APPELLE DE FONCTION SELON TYPE ET MESSAGE!!!        ##
                ##                      PAR EXEMPLE:                                      ##                         
                ## if type == "0x02":                                                     ##
                ##     if message == "rajouter_dose":                                     ##
                ##         rajouter_dose()                                                ##
                ##     elif message == "retirer_dose":                                    ##
                ##         retirer_dose()                                                 ## 
                ##....ect (ne pas oublier gestion des erreurs, comme type invalide...ect) ##                                               
                ############################################################################
        except:
            display.scroll("Erreur message")
            continue
           
