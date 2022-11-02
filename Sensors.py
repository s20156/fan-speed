import psutil


class Sensors:
    """
    Class generating worker object to get data from system sensors
    """
    def __init__(self):
        pass

    @staticmethod
    def get_cpu_percentage():
        """
        Static method to get CPU usage in percents
        :return: cpu percentage taken during testing for 1 second
        """
        return psutil.cpu_percent(1)

    @staticmethod
    def get_temp():
        """
        Static method to get system temperatures in Celsius degrees
        :return: dictionary with given metrics for temperatures of several components
        """
        return psutil.sensors_temperatures()