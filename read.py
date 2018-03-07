from typing import List
from typing import Dict
from typing import Tuple

import matplotlib.pyplot as plt
import time

path = "/media/mrd/Data/twirrelog_2018-03-05T161052+0100.tlog"


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

    def get_sensor_dict(self) -> Dict[str, Dict[str, Dict[float, float]]]:
        return self.sensor_dict

    def get_actuator_dict(self):
        return self.actuator_dict

    def get_timevalue_lists(self, devname: str, valuename: str, isactuator: bool, fromtime: float=0, tilltime: float=1e99) -> Tuple[List[float], List[float]]:
        if isactuator:
            readings = self.actuator_dict[devname][valuename]
        else:
            readings = self.sensor_dict[devname][valuename]

        reading_times = [t for t in sorted(readings.keys()) if fromtime <= t < tilltime]
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
                self.__get_dict_for_value(dev_dict, key)[time / 1000000.0] = value

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

from_time = 60.0
till_time = 80.0


def show_control_plot(err_name, err_dev, err_value, err_isactuator, ctl_dev, ctl_value, ctl_isactuator, fromtime, tilltime, scale_err: float=1, offset_err: float=0):
    error_time, error_value = log.get_timevalue_lists(err_dev, err_value, err_isactuator, fromtime=fromtime, tilltime=tilltime)
    error_value = [x * scale_err + offset_err for x in error_value]
    ctl_time, ctl_value = log.get_timevalue_lists(ctl_dev, ctl_value, ctl_isactuator, fromtime=fromtime, tilltime=tilltime)

    fig, ax1 = plt.subplots()
    color = 'tab:red'
    ax1.set_xlabel('time (s)')
    ax1.set_ylabel(err_name + ' error (m)', color=color)
    ax1.plot((from_time, till_time), (0, 0), '-', color=color)
    ax1.plot(error_time, error_value, color=color)
    ax1.tick_params(axis='y', labelcolor=color)

    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

    color = 'tab:blue'
    ax2.set_ylabel('control output', color=color)  # we already handled the x-label with ax1
    ax2.step(ctl_time, ctl_value, color=color, where='post')
    ax2.plot((from_time, till_time), (0, 0), '-', color=color)
    ax2.scatter(ctl_time, ctl_value, color=color, marker='.')
    ax2.tick_params(axis='y', labelcolor=color)

    fig.tight_layout()  # otherwise the right y-label is slightly clipped
    plt.show()


plt.ion()
show_control_plot('altitude', 'sonar1', 'firstDistance', False, 'naza', 'gaz', True, from_time, till_time, scale_err=0.01, offset_err=-1.1)
show_control_plot('horizontal', 'lns', 'localTgtPositionRight', True, 'naza', 'roll', True, from_time, till_time)
show_control_plot('yaw', 'lns', 'localTgtPositionYaw', True, 'naza', 'yaw', True, from_time, till_time)
show_control_plot('distance', 'lns', 'localTgtPositionForward', True, 'naza', 'pitch', True, from_time, till_time)
while True:
    plt.pause(0.001)
    time.sleep(0.2)
