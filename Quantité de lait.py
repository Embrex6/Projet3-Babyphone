from microbit import *

# quantité totale de doses consommées
quantite_lait = 0

def modifie_lait(action, valeur):
    """
    Quantite de lait que le bébé a bu 
    """
    if action == "plus":
        valeur = valeur + 1

    elif action == "moins":
        if valeur > 0:
            valeur = valeur - 1

    elif action == "reset":
        valeur = 0

    return valeur


display.scroll("0")

while True:

    if button_a.was_pressed():
        quantite_lait = modifie_lait("plus", quantite_lait)
        display.scroll(str(quantite_lait))

    if button_b.was_pressed():
        quantite_lait = modifie_lait("moins", quantite_lait)
        display.scroll(str(quantite_lait))

    if button_a.is_pressed() and button_b.is_pressed():
        quantite_lait = modifie_lait("reset", quantite_lait)
        display.scroll("0")
        sleep(500)  # évite plusieurs resets
