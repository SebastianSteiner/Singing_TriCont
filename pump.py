#!/usr/bin/env python
# /* ============================================================================ */
# /*                                                                              */
# /*   pump.py                                                                    */
# /*   (c) 2017 Sebastian Steiner, The Cronin Group, University of Glasgow        */
# /*                                                                              */
# /*   TriContinent C3000 pump module.                                            */
# /*   Contains all functions for actuating TriContinent pumps.                   */
# /*                                                                              */
# /*   For style guide used see http://xkcd.com/1513/                             */
# /*                                                                              */
# /* ============================================================================ */

# system imports
import serial
import time

# initialisation direction ("Y" = input right, "Z" = input left)
initialisation_direction = "Z"

# fluidic port settings
inlet = "I"
outlet = "O"
bypass = "B"

# speed settings
top_velocity = 6000

# syringe parameters
syringe_size = 5  # mL
max_steps = 3000  # default for C3000 normal mode

# transfer parameters
stroke_volume = 5  # mL


# class definition
class Pump:
    def __init__(self, port):
        """Initialises the serial port for the pumps."""
        self.port = port
        self.connection = serial.Serial(timeout=1)
        self.connection.port = self.port

    def open(self):
        """Opens a connection."""
        self.connection.open()
        print("Opening connection on port" + str(self.port))

    def close(self):
        """Closes the connection again."""
        self.connection.close()
        print("Connection on port " + str(self.port) + " closed.")

    def is_open(self):
        """Checks if the port is open and returns the answer."""
        return self.connection.isOpen()

    def initialise(self, address):
        """Checks if the pump is initialised, if not does so."""
        if not self.is_initialized(address):
            out_data = '/' + str(address) + initialisation_direction + 'R\r'  # \r is 'carriage return', R executes
            if self.is_ready(address):
                self.connection.write(out_data.encode())
                print("Initialising pump " + str(address))

    def is_initialized(self, address):
        """Asks if the pump is initialised and waits for the answer.
        Returns TRUE or FALSE accordingly. Code snippet by Alon."""
        self.is_ready(address)
        out_data = '/' + str(address) + '?19R\r'
        while True:
            self.connection.write(out_data.encode())
            self.connection.flushInput()
            back = self.connection.readline()
            back = str(back)
            if '`' in back:
                state = back.split('`')[1][0]
                if state == '0':
                    return False
                elif state == '1':
                    return True

    def is_ready(self, address):
        """Waits until the pump is ready. Code snippet by Alon."""
        out_data = "/" + str(address) + "QR\r"
        while True:
            time.sleep(0.05)
            self.connection.write(out_data.encode())
            self.connection.flushInput()  # added to flush buffer from nonsense
            back = self.connection.readline()
            if 96 in back:  # 64 is @ (busy) and 48 is 0 (idle) 96 is ' which is also good
                return True

    def switch_valve(self, valve_position):
        """Returns the appropriate character for the desired valve position."""
        if valve_position == "inlet":
            return inlet
        elif valve_position == "outlet":
            return outlet
        else:
            pass  # todo: error handling

    def goto_position(self, abs_ml):
        """Returns the appropriate command string to send the pump to an absolute position.
        Calculates steps from mL in the process."""
        steps = int((max_steps / syringe_size) * abs_ml)
        if steps in range(max_steps + 1):
            return "A" + str(steps)
        else:
            pass  # todo: error handling

    def pump_rate(self, ml_per_min):
        """Returns the appropriate command string to set the pumping rate.
        Calculates Hz from mL/min in the process."""
        ml_per_step = int(syringe_size / max_steps)  # calculate volume of one step
        step_per_min = int(ml_per_min / ml_per_step)  # calculate steps per min from mL/min
        half_step_per_sec = int((2 * step_per_min) / 60)  # calculate Hz (half steps per second) from steps per min
        if ml_per_min == "default":  # if we can't be bothered
            return ""
        elif half_step_per_sec in range(top_velocity + 1):  # if we actually want to do this
            return "V" + str(half_step_per_sec)
        else:
            pass  # todo: error handling

    def repeat(self, number_of_repeats):
        """Returns the appropriate command string for multiple repeats."""
        return "G" + str(number_of_repeats)

    def transfer(self, address, direction, repeats):
        """Transfers a specified volume (stroke_volume) from inlet to outlet (direction "in")
        or from outlet to inlet (direction "out"). Can be repeated as often as needed."""
        if direction == "in":
            out_data = (
                "/"
                + str(address)
                + self.switch_valve("inlet")
                + self.goto_position(stroke_volume)
                + self.switch_valve("outlet")
                + self.goto_position(0)
                + self.repeat(repeats)
                + "R"
                + "\r"
            )
            if self.is_ready(address):
                self.connection.write(out_data.encode())
                print("Pump " + str(address) + " is transferring from inlet to outlet " + str(repeats) + " times.")
                self.is_ready(address)
                print("Done.")
        elif direction == "out":
            out_data = (
                "/"
                + str(address)
                + self.switch_valve("outlet")
                + self.goto_position(stroke_volume)
                + self.switch_valve("inlet")
                + self.goto_position(0)
                + self.repeat(repeats)
                + "R"
                + "\r"
            )
            if self.is_ready(address):
                self.connection.write(out_data.encode())
                print("Pump " + str(address) + " is transferring from inlet to outlet " + str(repeats) + " times.")
                self.is_ready(address)
                print("Done.")
        else:
            pass  # return error
