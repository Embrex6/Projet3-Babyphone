"""donc on va faire une fonction type chiffrement de vigenère: donc on a texte et on a clé(répétable en boucle),
chaque lettre du texte subit un décalage défini, grâce à notre clé(voir doc crypto vue en classe)

Bonus: comprendre la formule "position_chiffre = (position_car + position_cle) % 26", conseille avoir le tableau de virgenie devant soi, en gros le chiffrement
de virgenie consiste grace a la position de lettre cle et de lettre car(lettre du texte) davoir une nouvelle position, et cette position on peut se servir pour
avoir une nouvelle lettre qui est chiffree, par exemple lettre cle cest E, donc position 4, et lettre car cest D, donc position 3, 3 + 4, fait 7, 7 modulo 26
fait 7 (ainsi on sassure ne jamais depasse le cadre de lecture de l'alphabet), donc 7 correspond a la lettre H, voila notre lettre chiffré selon virgenie!
"""

def position_alphabet(lettre):
    """trouve la position d'une lettre dans l'alphabet
    """
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    for i in range(26):
        if alphabet[i] == lettre:
            return i
    return None


def alphabet_position(position):
    """trouve la lettre de l'alphabet depuis la position de celle-ci
    """
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return alphabet[position]


def chiffrement_vigenere(texte, cle):
    """faire en sorte que la cle soit TOUJOURS PLUS COURT que le texte
       et composé de lettre de l'alphabet
    """
    texte = texte.upper()
    cle = cle.upper()
    l = "" #contient caractère chiffré
    cle_index = 0 #correspondance position entre lettre texte et lettre clé, puisque len cle plus petit que len texte, bouclé!
    
    for car in texte:
        if car.isalpha():
            if cle_index >= len(cle):
                cle_index = 0 #on gros à chaque fois que notre lecture du texte avec la clé a atteint len(cle), il faut donc boucler, et recommencer la lecture
                
            position_car = position_alphabet(car) #donc on obtient un entier
            position_cle = position_alphabet(cle[cle_index])#donc on obtient un entier qui correspond a la position de la lettre de la cle
            position_chiffree = (position_car + position_cle) % 26 #c'est un truc mathématique, modulo 26, permet de rester dans l'alphabet
            lettre_chiffree = alphabet_position(position_chiffree) #permet cette foi ci de retourner la lettre qui a donc subit le décalage(chiffrée)
            l += lettre_chiffree

            cle_index += 1
        else:
            l += car

    return l
        
def dechiffrement_vigenere(texte_chiffree, cle):
    texte_chiffree = texte_chiffree.upper()
    cle = cle.upper()
    l = ""
    cle_index = 0

    for car in texte_chiffree:
        if car.isalpha():
            if cle_index >= len(cle):
                cle_index = 0

            position_car = position_alphabet(car)
            position_cle = position_alphabet(cle[cle_index])
            position_dechiffree = (position_car - position_cle) % 26 #même principe sauf qu'ici position_car correspond à position lettre déjà chiffré comme précèdemment
            lettre_dechiffree = alphabet_position(position_dechiffree)
            l += lettre_dechiffree

            cle_index += 1
        else:
            l += car

    return l


