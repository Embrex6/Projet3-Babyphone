from microbit import *
import radio
import random
import music

radio.config(channel=1, group=1)
radio.on()

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


#demande pour une nouvelle connexion avec l'autre microbits
def etablir_connexion(cle):
    """
        Etablissement de la connexion avec l'autre micro:bit
        Si il y a une erreur, la valeur de retour est vide
        
        pre: cle est chaine de caractère
        
        post: return en chaine de caractère la reponse au challenge via la fct: calcul_reponse_challenge
    """
    try:
        challenge = str(random.randint(1000, 9999))
        new_nonce = str(random.randint(100, 999))
        contenue = new_nonce + ":" + challenge
        envoie_via_TLV(cle, "0x01", contenue)
        
        type, longueur, contenu = recevoir_message(cle)
        if contenu == "" or type != "0x01"
            return ""
        nonce, reponse = contenu.split(":")
        if type == "0x01" and reponse == calcul_reponse_challenge(challenge):
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
    return True
