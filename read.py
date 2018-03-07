from typing import List
from typing import Dict
from typing import Tuple

import matplotlib.pyplot as plt

path = "D:\\twirrelog_2018-03-05T161052+0100.tlog"


class LogfileParser:
    def __init__(self, logpath):
        file = open(logpath, 'r')

        lines = file.readlines()
        lines = [x.strip() for x in lines]  # strip indent, newline
        lines = [x[:x.find('#')] if ('#' in x) else x for x in lines]  # strip comments
        self.lines = [x for x in lines if len(x) > 0]  # remove empty lines
        self.curline = -1
        self.lastline = len(self.lines) - 1
        self.sensor_dict = {}
        self.actuator_dict = {}
        self.__process_file()

    def get_sensor_dict(self) -> Dict[str, Dict[str, Dict[int, float]]]:
        return self.sensor_dict

    def get_actuator_dict(self):
        return self.actuator_dict

    def get_timevalue_lists(self, devname: str, valuename: str, isactuator: bool) -> Tuple[List[int], List[float]]:
        if isactuator:
            readings = self.actuator_dict[devname][valuename]
        else:
            readings = self.sensor_dict[devname][valuename]

        reading_times = sorted(readings.keys())
        reading_values = [readings[t] for t in reading_times]

        return reading_times, reading_values

    def __haveline(self) -> bool:
        return self.curline < self.lastline

    def __fetchline(self) -> List[str]:
        self.curline += 1
        return self.lines[self.curline].split()

    @staticmethod
    def __get_dict_for_device(group_dict, name):
        if name not in group_dict:
            group_dict[name] = {}
        return group_dict[name]

    @staticmethod
    def __get_dict_for_value(dev_dict, name):
        if name not in dev_dict:
            dev_dict[name] = {}
        return dev_dict[name]

    def __process_create(self, parts, time):
        if len(parts) < 1:
            print('too short create statement at', time, 'create')
        elif parts[0] == 'binfile':
            # todo: handle binfile create
            pass
        else:
            print('unrecognized create statement at', time, 'create', parts)

    def __process_actuators(self, parts, time):
        # todo: handle actuator list better
        level = 1
        while level > 0 and self.__haveline():
            line = self.__fetchline()
            if '{' in line:
                level += 1
            if '}' in line:
                level -= 1

    def __process_sensors(self, parts, time):
        # todo: handle sensor list better
        level = 1
        while level > 0 and self.__haveline():
            line = self.__fetchline()
            if '{' in line:
                level += 1
            if '}' in line:
                level -= 1

    def __process_valueupdate(self, dev_dict, time):
        level = 1
        while level > 0 and self.__haveline():
            line = self.__fetchline()

            if '{' in line:
                level += 1
            if '}' in line:
                level -= 1

            if len(line) == 1 and line[0] != '}':
                kv = line[0].split(':')
                if len(kv) != 2:
                    print('unrecognized kv: ', kv, 'at', time)
                    continue
                key = kv[0]
                try:
                    value = float(kv[1])
                except ValueError:
                    print('illegal kv:', kv)
                    continue
                self.__get_dict_for_value(dev_dict, key)[time] = value

    def __process_actuate(self, parts, time):
        if len(parts) < 1:
            print('empty actuate at', time)
            return

        dev_name = parts[0]
        dev_dict = self.__get_dict_for_device(self.actuator_dict, dev_name)
        self.__process_valueupdate(dev_dict, time)
        pass

    def __process_sense(self, parts, time):
        if len(parts) < 1:
            print('empty sense at', time)
            return

        dev_name = parts[0]
        dev_dict = self.__get_dict_for_device(self.sensor_dict, dev_name)
        self.__process_valueupdate(dev_dict, time)
        pass

    def __process_line(self, parts, time):
        if len(parts) < 1:
            print('no action in line at', time)
        elif parts[0] == 'init':
            pass
        elif parts[0] == 'create':
            self.__process_create(parts[1:], time)
        elif parts[0] == 'actuators':
            self.__process_actuators(parts[1:], time)
        elif parts[0] == 'sensors':
            self.__process_sensors(parts[1:], time)
        elif parts[0] == 'actuate':
            self.__process_actuate(parts[1:], time)
        elif parts[0] == 'sense':
            self.__process_sense(parts[1:], time)

    def __process_file(self):
        while self.__haveline():
            parts = self.__fetchline()

            if parts[0].isdigit():
                timestamp = int(parts[0])
            else:
                print('unexpected line', parts)
                continue

            self.__process_line(parts[1:], timestamp)

log = LogfileParser(path)

altitude_time, altitude_value = log.get_timevalue_lists('sonar1', 'firstDistance', False)
plt.scatter(altitude_time, altitude_value)
plt.show()
