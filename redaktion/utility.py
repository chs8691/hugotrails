import datetime
import os

from pytz import timezone
from timezonefinder import TimezoneFinder

log_switch = False
out_file = 'out.txt'
posts_dir = "../content/post"
devices_dir = "../content/devices"
device_file_name = "_index.md"
post_file_name = "index.md"


def z_date_to_locale_dt(utc_date_z_string, latitude, longitude):
    """
    Converts from a UTC datetime string in Z-format to a locale date time object for the give position in ISO8601 format.
    E.g. 2020-06-31T06:39:19.000Z --> 2020-06-31T04:39:19+02:00
    :param utc_date_z_string: Z-ended String
    :param latitude:  as float, can be None
    :param longitude:  as float, can be None
    :returns: datetime object, e.g. for '2018-01-27T05:32:54+01:00'
    """
    utc_dt = convert_z_ended_date_to_dt(utc_date_z_string)
    tf = TimezoneFinder(in_memory=True)

    if latitude is None or longitude is None:
        debug(f"No Position data to calculate locale date for {utc_date_z_string}")
        return convert_z_ended_date_to_dt(utc_date_z_string)

    debug(f"Locale for UTC={utc_date_z_string} at lon={longitude}, lat={latitude}")
    my_zone = timezone(tf.timezone_at(lng=longitude, lat=latitude))

    return utc_dt.astimezone(my_zone)


def z_date_to_locale_date(utc_date_z_string, latitude, longitude):
    """
    Converts from a UTC datetime string in Z-format to a locale date time for the give position in ISO8601 format.
    E.g. 2020-06-31T06:39:19.000Z --> 2020-06-31T04:39:19+02:00
    :param utc_date_z_string: Z-ended String
    :param latitude:  as float, can be None
    :param longitude:  as float, can be None
    :returns: ISO formatted String, e.g. '2018-01-27T05:32:54+01:00'
    """
    ret = z_date_to_locale_dt(utc_date_z_string, latitude, longitude).strftime("%Y-%m-%dT%H:%M:%S%z")

    debug(f"Convert {utc_date_z_string} --> {ret}")

    return ret


def convert_z_ended_date_to_dt(z_ended_dt):
    """
    Returns datetime object from a TCX datetime
    :param z_ended_dt:  Z-ended String, e.g. 2020-06-31T06:39:19.000Z
    :return: datetime object with UTC timezone
    """
    dt = datetime.datetime.strptime(z_ended_dt[0:19], "%Y-%m-%dT%H:%M:%S")

    return datetime.datetime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, tzinfo=datetime.timezone.utc)


def z_date_to_utc_date(utc_datetime_z_string):
    """
    Converts from a UTC datetime string in Z-format to a valid UTC date time in ISO8601 format.
    E.g. 2020-06-31T06:39:19.000Z --> 2020-06-31T06:39:19+00:00
    :param utc_datetime_z_string: Z-ended String
    :returns: ISO formatted String, e.g. '2018-01-27T05:32:54+01:00'
    """
    utc_dt = convert_z_ended_date_to_dt(utc_datetime_z_string)

    ret = utc_dt.strftime("%Y-%m-%dT%H:%M:%S%z")

    debug(f"Convert {utc_datetime_z_string} --> {ret}")

    return ret


def build_post_path(post_datetime):
    """
    Build the path to the post directory for a given timestamp (==ID)
    :param post_datetime: A datetime object
    :return: String with the path to the directory, e.g. "/hugo/content/post/2020/20203112-105959
    """
    post_dir = build_post_key(post_datetime)
    year = datetime.datetime.strftime(post_datetime, "%Y")

    return os.path.join(posts_dir, year, post_dir)


def build_post_key(post_datetime):
    return datetime.datetime.strftime(post_datetime, "%Y%m%d-%H%M%S")


def set_log_switch(value):
    global log_switch
    log_switch = value


# def progress_start(max):
#     digits = len(str(max))
#     act = 0
#     out(f"{act:{digits}}/{max:{digits}}")
#
#
# def progress_update(act, max):
#     digits = len(str(max))
#     out(f"{act:{digits}}/{max:{digits}}")
#

def debug(message):
    """
        Only switched on for development
    """
    if log_switch:
        out(f"LOG {message}")


def init_out():
    if os.path.exists(out_file):
        os.remove(out_file)


def warn(message):
    """
    Print a WARN to console - and maybe later to file
    """
    text = f"WARN {message}"
    print(text)
    with open(out_file, mode='a') as file_object:
        print(text, file=file_object)


def out(message):
    """
    Print to console - and maybe later to file
    """
    print(message)
    with open(out_file, mode='a') as file_object:
        print(message, file=file_object)


def error(message):
    """
    log and exit
    """
    out(f"ERROR {message}")
    exit(1)
