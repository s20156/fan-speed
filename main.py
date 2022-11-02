import datetime
import click
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

from Sensors import Sensors


"""
Realizacja projektu:
* Cezary Malejka
* Mateusz Grube

Projekt ma na celu przedstawienie działania biblioteki skfuzzy implementującej algorytmy logiki rozmytej w praktyce.
Praktyczny aspekt projektu opiera się na wymogu kontroli temperatury kluczowych podzespołów komputera w celu zabezpieczenia przed ich uszkodzeniem.
Projekt realizuje logikę rozmytą opierając się na parametrach:
* Zużycie procesora
* Temperatura procesora
* Aktualna godzina

Instrukcja:
W celu wyświetlenia pomocy do projektu należy projekt uruchomić komendą
python3 main.py

Projekt pozwala na wykorzystanie dwóch komend:
* calc - program przyjmuje wartości w postaci inputu w terminalu
* comp - program pobiera dane z aktualnych wartości z sensorów podpiętych do systemu.
UWAGA: funkcja comp została przetestowana na sprzęcie Asus ROG Zephyrus G14 w systemie Ubuntu 22.04. 
Pobieranie danych z sensora może nie działać poprawnie na innym sprzęcie.
"""

class FanSpeed:
    """
    Main project class
    Used to create a worker object to fuzzyfy inputs, compute and defuzzyfy output of fan speed computation
    Bases the fuzzy logic on parameters of current CPU temp, CPU usage and current time (to avoid loud fans during night hours)
    """
    def __init__(self):
        # Create fuzzy variables
        self.temp = ctrl.Antecedent(np.arange(0, 95, 5), 'temperature')
        self.cpu_percent = ctrl.Antecedent(np. arange(0, 95, 5), 'percentage')
        self.time = ctrl.Antecedent(np.arange(0, 24, 1), 'time')
        self.cpu_fan = ctrl.Consequent(np.arange(1000, 4500, 100), 'cpu_fan')

        # Populate the fuzzy variables with terms
        self.temp.automf(3, "quant")
        self.cpu_percent.automf(3, "quant")
        self.time.automf(2, "quant", ["low", "high"])

        self.cpu_fan["low"] = fuzz.trimf(self.cpu_fan.universe, [1000, 1000, 2000])
        self.cpu_fan["medium"] = fuzz.trimf(self.cpu_fan.universe, [1000, 2000, 4500])
        self.cpu_fan["high"] = fuzz.trimf(self.cpu_fan.universe, [2000, 4500, 4500])
        
        # create rules
        
        self.rules = [
            ctrl.Rule(self.temp["low"] & self.cpu_percent["low"], self.cpu_fan["low"]),
            ctrl.Rule(self.temp["average"] & self.cpu_percent["average"] & self.time["low"], self.cpu_fan["high"]),
            ctrl.Rule(self.temp["average"] & self.cpu_percent["average"] & self.time["high"], self.cpu_fan["low"]),
            ctrl.Rule(self.temp["high"] & self.cpu_percent["high"], self.cpu_fan["high"]),
        ]


    @staticmethod
    def parse_time(time):
        """
        Function to return time in a simple numeric notation
        :param time: time in datetime.time() format
        :return: parsed time to match [6-23] = [0 - 17], [0-5] = [18 - 23]
        """
        if time.hour >= 6:
            return time.hour - 6
        else:
            return 18 + time.hour

    def fuzzy(self, temp, cpu_percent, time):
        """ Fuzzy computation and defuzzyfication function
        :param temp: CPU Temperature
        :param cpu_percent: Current CPU usage in %
        :param time: current hour parsed using parse_time method
        :return: Deffuzzyfied cpu fan speed
         """
        cpu_fan_ctrl = ctrl.ControlSystem(self.rules)
        cpu_fan = ctrl.ControlSystemSimulation(cpu_fan_ctrl)
        cpu_fan.input["temperature"] = temp
        cpu_fan.input["percentage"] = cpu_percent
        cpu_fan.input["time"] = time
        cpu_fan.compute()
        return cpu_fan.output["cpu_fan"]


fan_speed = FanSpeed()
sensors = Sensors()


@click.group()
def calculate():
    pass


@calculate.command()
@click.option("--temp", prompt="Temperature: ", help="Current CPU temp", default=1)
@click.option("--percent", prompt="CPU usage [%]: ", help="Current CPU usage", default=1)
@click.option("--time", default=fan_speed.parse_time(datetime.datetime.now().time()), prompt="Current hour", help="Current hour without minutes and seconds")
def calc(temp, percent, time):
    output = fan_speed.fuzzy(temp, percent, time)
    print(output)


@click.group()
def machine():
    pass


@machine.command()
def comp():
    cpu_percent = sensors.get_cpu_percentage()
    print("CPU Usage: " + str(cpu_percent))
    cpu_temp = sensors.get_temp()['acpitz'][0].current
    print("CPU Temperature: " + str(cpu_temp) + "C")
    time = fan_speed.parse_time(datetime.datetime.now().time())
    print("Current time: " + str(time))
    output = fan_speed.fuzzy(cpu_temp, cpu_percent, time)
    print(output)


cli = click.CommandCollection(sources=[calculate, machine])

if __name__ == "__main__":
    cli()
