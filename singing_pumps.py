#!/usr/bin/env python
# /* ============================================================================ */
# /*                                                                              */
# /*   singing_pumps.py                                                           */
# /*   (c) 2017 Sebastian Steiner                                                 */
# /*                                                                              */
# /*   TriCont pump playing music.                                                */
# /*   Because reasons.                                                           */
# /*                                                                              */
# /*   For style guide used see http://xkcd.com/1513/                             */
# /*                                                                              */
# /* ============================================================================ */

import pump
import time

# port and address, adjust as needed
pump_port = "COM5"
pump_adress = 1

# path to text file containing the notes. Should ideally be an absolute path.
sheet_music_file = "Tetris.txt"

# musical intelligence
bpm = 240

frequencies = {
    "p": 0,
    "f'": 175,
    "g'": 196,
    "a'": 220,
    "c": 262,
    "d": 294,
    "e": 330,
    "f": 349,
    "g": 392,
    "a": 440,
    "ab": 415,
    "a#": 466,
    "b": 494,
    "C": 523,
    "D": 587,
    "E": 659,
    "F": 698,
    "G": 784,
    "A": 880,
    "B": 988
}

# initialise direction and step counter
direction = "P"
total_steps = 0

# instantiate and initialise pump
p = pump.Pump(pump_port)
p.open()
p.initialise(pump_adress)
p.is_ready(pump_adress)
time.sleep(1)

with open(sheet_music_file) as f:
    for line in f:
        # parse notes
        content = line.split("-")
        note = content[0]
        length = content[1]

        # calculate frequencies
        frequency = frequencies[note]
        steps = int((frequency * 120) / (bpm * int(length)))

        # handle dead centres
        if direction == "P":
            if steps + total_steps > 3000:
                direction = "D"
            else:
                total_steps += steps

        if direction == "D":
            if total_steps - steps < 0:
                direction = "P"
            else:
                total_steps -= steps

        if note == p:  # handle pauses
            secs = (960 / (int(length) * bpm))
            time.sleep(secs)
        else:  # handle notes
            out_data = (
                "/" +
                str(pump_adress) +
                "V" +
                str(frequency) +
                direction +
                str(steps) +
                "R" +
                "\r"
            )
            print(out_data)
            p.connection.write(out_data.encode())
            p.is_ready(pump_adress)

# home pump at the end
p.is_ready(pump_adress)
p.connection.write((
    "/" +
    str(pump_adress) +
    "V" +
    "6000" +
    "A" +
    "0" +
    "R\r"
).encode())
