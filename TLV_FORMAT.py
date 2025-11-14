"""
Donc avant d'envoyer un message via 'radio send', il faut transmettre sous forme tlv, si par exemple le babyphone bebe
va transmettre un message pour dire que le bébé il est agité au babyphone parent, il doit utilise la fonction tlv_format
pour envoyer au bon format, puis le babyphone parent recoit via radio receive, et doit utiliser la fonction reconstruire
pour transformer le message tlv, en trois variable utilisable, ici donc, type pour état, 5 pour longeur et agitée
pour valeur

"""
def tlv_format(type, valeur): 
    longueur = len(valeur)
    print(f"{type}|{longueur}|{valeur}")
    return f"{type}|{longueur}|{valeur}"

def reconstruire(message): 
    try:
        type, longueur, valeur = message.split("|")
        longueur = int(longueur)
        if longueur != len(valeur):
            print(None)
            return None
        print(type, longueur, valeur)
        return type, longueur, valeur
    except:
        print(None)
        return None


message = tlv_format("état", "agité")
reconstruire(message)

