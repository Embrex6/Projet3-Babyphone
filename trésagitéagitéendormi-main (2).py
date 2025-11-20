from microbit import *
import radio
import music

# CHOOSE ROLE: "child" = baby, "parent" = parent
ROLE = "child"   # change to "parent" on the other micro:bit

radio.on()
radio.config(channel=1)

while True:

    # ----------------------
    # CHILD MODE
    # ----------------------
    if ROLE == "child":

        # simple movement detection (x-axis)
        x = accelerometer.get_x()

        if abs(x) < 2000:
            state = "A"       # Asleep
            display.show("A")
            sleep(3000)       # display 3 seconds
        elif abs(x) < 6000:
            state = "G"       # Agitated
            display.show("G")
            sleep(3000)
        else:
            state = "T"       # Very Agitated
            display.show("T")
            sleep(3000)
            # play music ONLY if very agitated
            music.play(['C5','C5'])

        # send state to parent
        radio.send(state)


    # ----------------------
    # PARENT MODE
    # ----------------------
    else:
        message = radio.receive()

        if message:
            display.show(message)

            # optional sound for very agitated
            if message == "T":
                music.play(['C5','C5'])

            sleep(3000)   # keep message displayed 3 seconds
            display.clear()

        sleep(100)  # short pause for responsiveness

