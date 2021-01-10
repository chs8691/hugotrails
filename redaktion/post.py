import datetime
import os
import re
import shutil

import toml

from utility import debug, convert_z_ended_date_to_dt, z_date_to_locale_date, z_date_to_utc_date, devices_dir


def read_devices():
    """
    Read device file content from an existing file
    :file: Path of the file as String
    :return: Dictinary with device toml object, key is devices directory name
    """
    ret = dict()
    for dir in [d for d in os.listdir(devices_dir) if os.path.isdir(os.path.join(devices_dir, d))]:
        data = read_toml_file(os.path.join(devices_dir, dir, "_index.md"))
        ret[dir] = data

    return ret


def read_toml_file(file):
    """
    Read file with toml formatted data
    :file: Path of the file as String
    :return: New toml object
    """
    with open(file, "r") as f:
        marker = re.compile("^\\+\\+\\+")
        started = False
        data = ""
        for line in f:
            if re.match(marker, line):
                if started:
                    break
                else:
                    started = True
                    continue
            data = f"{data}{line}"

        return toml.loads(data)


def read_post_file(file):
    """
    Read pst file content from an existing file
    :file: Path of the file as String
    :return: New Post, initialized with post's params from file. TOML key and values are turned to lowercase
    """
    data = read_toml_file(file)

    return Post(file, data)


class Post:
    """
    Holds all data for index.md of an activity post
    """
    ACTIVITY = 'activity'
    ACTIVITY_SPORT = 'activity_sport'
    ALTITUDE_MAX__M = 'altitude_max__m'
    ALTITUDE_MIN__M = 'altitude_min__m'
    ASCENT__M = 'ascent__m'
    AVERAGE_HEART_RATE__BPM = 'average_heart_rate__bpm'
    AVERAGE_SPEED__KM_PER_H = 'average_speed__km_per_h'
    BASE = 'base'
    CATEGORY = 'category'
    DATE = 'date'
    DATE_UTC = 'date_utc'
    DESCENT__M = 'descent__m'
    DESCRIPTION = 'description'
    DEVICE = 'device'
    DEVICE_IN_TOPICS = 'device_in_topics'
    DISTANCE__M = 'distance__m'
    DRAFT = 'draft'
    MAXIMUM_HEART_RATE__BPM = 'maximum_heart_rate__bpm'
    PACE__S_PER_KM = 'pace__s_per_km'
    SPORT = 'sport'
    TITLE = 'title'
    TOPIC = 'topic'
    TOTAL_TIME__S = 'total_time__s'
    UTENSILS = 'utensils'
    YEAR = 'year'

    BASE_TCX = 'tcx'

    CATEGORY_CYCLING = 'cycling'
    CATEGORY_GYM = 'gym'
    CATEGORY_HIKING = 'hiking'
    CATEGORY_RUNNING = 'running'
    CATEGORY_OTHERS = 'others'

    TOPIC_DIE_RUNDE_STUNDE = 'die-runde-stunde'
    TOPIC_FITNESS = 'fitness'

    def __init__(self, file_name, initial_data):

        # index.md path
        self.file_name = file_name

        # original data
        self.initial_data = initial_data

        # new data
        self.data = dict()
        self.data = self.initial_data.copy()
        # self._init(self.ACTIVITY)
        # self._init(self.ACTIVITY_SPORT)
        # self._init_optional(self.ASCENT__M, self.ALTITUDE_MAX__M)
        # self._init_optional(self.ASCENT__M, self.ALTITUDE_MIN__M)
        # self._init_optional(self.ASCENT__M, self.ASCENT__M)
        # self._init_optional(self.AVERAGE_HEART_RATE__BPM, self.AVERAGE_HEART_RATE__BPM)
        # self._init_optional(self.DISTANCE__M, self.AVERAGE_SPEED__KM_PER_H)
        # self._init(self.BASE)
        # self._set_category_by_activity_sport(self.CATEGORY)
        # self._init(self.DATE)
        # self._init(self.DATE_UTC)
        # self._init_optional(self.ASCENT__M, self.DESCENT__M)
        # self._init_optional(self.DESCRIPTION, self.DESCRIPTION)
        # self._init_optional(self.DEVICE, self.DEVICE)
        # self._init_optional(self.DEVICE, self.DEVICE_IN_TOPICS)
        # self._init_optional(self.DISTANCE__M, self.DISTANCE__M)
        # self._init(self.DRAFT)
        # self._init_optional(self.AVERAGE_HEART_RATE__BPM, self.MAXIMUM_HEART_RATE__BPM)
        # self._init_optional(self.DISTANCE__M, self.PACE__S_PER_KM)
        # self._init_optional(self.DEVICE, self.SPORT)
        # self._init(self.TITLE)
        # self._init(self.TOPIC)
        # self._init(self.TOTAL_TIME__S)
        # self._init_optional(self.UTENSILS, self.UTENSILS)
        # self._init(self.YEAR)

    def get_dir(self):
        """
        The name of the directory of this post, e.g. "20201231-172153"
        :return: String with directory name (no path)
        """
        return os.path.basename(os.path.dirname(self.file_name))

    def get_date(self):
        """
        Returns the locale date as a formatted String "%Y-%m-%dT%H:%M:%S"
        :return: Date String, e.g. "2004-12-31T07:03:38"
        """
        return self.data[self.DATE]

    def get_datetime(self):
        """
        Returns the locale date as a date time object
        :return: Date String, e.g. "2004-12-31T07:03:38"
        """
        return datetime.datetime.strptime(self.data[self.DATE], "%Y-%m-%dT%H:%M:%S%z")

    def get_datetime_utc(self):
        """
        Returns the locale date as a date time object
        :return: Date String, e.g. "2004-12-31T07:03:38"
        """
        return datetime.datetime.strptime(self.data[self.DATE_UTC], "%Y-%m-%dT%H:%M:%S%z")

    def _init(self, key):
        """
        Copies item from initial_data into data
        :param key: Item's key
        """
        if key in self.initial_data:
            self.data[key] = self.initial_data[key]
        else:
            self.data[key] = None

    def _init_optional(self, master_key, key):
        """
        Copies item from initial_data into data, if an other item is in initial_data exists
        :param master_key: Master item's key
        :param key: Item's key
        """
        if master_key in self.initial_data:
            self._init(key)

    def _set_category_by_activity_sport(self, activity_sport):
        if activity_sport == 'biking':
            return self.CATEGORY_CYCLING
        elif activity_sport == 'running':
            return self.CATEGORY_RUNNING
        else:
            return self.CATEGORY_HIKING

    def _set(self, key, value):
        """
        Set item in data
        :param key: Item's key
        """
        self.data[key] = value

    def _set_optional(self, switch, key, value):
        """
        Set item in data, if switch is True. Removes existing item, if switch is False
        :param switch: True of false
        :param key: Item's key
        """
        if switch:
            self._set(key, value)
        elif key in self.data:
            self.data.pop(key)

    def set_tcx_data(self, tcxparser, file):
        """
        Set all tcx relevant fields in data. Optional items will be removed, if missing in tcx
        :param tcxparser: Tcxparser
        :param file: File path
        """
        self._set(self.ACTIVITY, os.path.basename(file))
        self._set_optional(tcxparser.has_altitude, self.ALTITUDE_MAX__M, int(tcxparser.altitude_max))
        self._set_optional(tcxparser.has_altitude, self.ALTITUDE_MIN__M, int(tcxparser.altitude_min))
        self._set_optional(tcxparser.has_altitude, self.ASCENT__M, int(tcxparser.ascent))
        self._set_optional(tcxparser.has_hr, self.AVERAGE_HEART_RATE__BPM, tcxparser.hr_avg)
        self._set(self.BASE, self.BASE_TCX)
        self._set(self.CATEGORY, self._set_category_by_activity_sport(tcxparser.activity_type))
        self._set(self.DATE, z_date_to_locale_date(tcxparser.started_at, tcxparser.latitude, tcxparser.longitude))
        self._set(self.DATE_UTC, z_date_to_utc_date(tcxparser.started_at))
        self._set_optional(tcxparser.has_altitude, self.DESCENT__M, int(tcxparser.descent))
        # self.data[self.DESCRIPTION]
        # self.data[self.DEVICE]
        # self.data[self.DEVICE_IN_TOPICS]
        self._set_optional(tcxparser.has_distance, self.DISTANCE__M, int(tcxparser.distance))
        self._set(self.DRAFT, True)
        self._set_optional(tcxparser.has_hr, self.MAXIMUM_HEART_RATE__BPM, tcxparser.hr_max)
        self._set(self.ACTIVITY_SPORT, tcxparser.activity_type)
        self._set_optional(tcxparser.has_distance, self.PACE__S_PER_KM, tcxparser.pace)
        # self._set(self.SPORT]
        self._set(self.TITLE, os.path.basename(file).split('.')[0])
        # self._set(self.TOPIC]
        self._set(self.TOTAL_TIME__S, int(tcxparser.duration))
        self._set_optional(tcxparser.has_distance, self.AVERAGE_SPEED__KM_PER_H, round(tcxparser.velocity_average, 2))
        # self._set(self.UTENSILS]
        self._set(self.YEAR, convert_z_ended_date_to_dt(tcxparser.started_at).strftime("%Y"))

    def save(self):
        """
        Save existing file with post data
        :return:
        """
        debug(f"Saving post {self.file_name}")
        with open(self.file_name, "w") as f:
            f.writelines([
                "+++\n",
                f"{toml.dumps(self.data)}",
                "+++\n",
            ])
