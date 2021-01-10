"Simple parser for Garmin TCX files."
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import time
from datetime import datetime

from lxml import objectify

from utility import debug

namespace = 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2'


class TCXParser:

    def __init__(self, tcx_file):
        tree = objectify.parse(tcx_file)
        self.root = tree.getroot()
        self.activity = self.root.Activities.Activity

    @property
    def has_hr(self):
        return len(self.hr_values()) > 0

    @property
    def has_distance(self):
        return len(self.distance_values()) > 0

    def hr_values(self):
        return [int(x.text) for x in self.root.xpath('//ns:HeartRateBpm/ns:Value', namespaces={'ns': namespace})]

    def altitude_points(self):
        return [float(x.text) for x in self.root.xpath('//ns:AltitudeMeters', namespaces={'ns': namespace})]

    def position_values(self):
        return [
            (float(pos.LatitudeDegrees.text),
             float(pos.LongitudeDegrees.text))
            for pos in self.root.xpath('//ns:Trackpoint/ns:Position', namespaces={'ns': namespace})]

    def distance_values(self):
        return self.root.findall('.//ns:Trackpoint/ns:DistanceMeters', namespaces={'ns': namespace})

    def time_values(self):
        return [x.text for x in self.root.xpath('//ns:Time', namespaces={'ns': namespace})]

    def cadence_values(self):
        return [int(x.text) for x in self.root.xpath('//ns:Cadence', namespaces={'ns': namespace})]

    def first_position(self):
        """
        Returns the very first position item
        :return: Tuple with lat, lon or None, if no position found
        """
        if len(self.position_values()) == 0:
            return None
        else:
            return self.position_values()[0]

    @property
    def latitude(self):
        """
        Returns the latitude from the first Position item
        :return: float or None, if no Position item found
        """
        if self.first_position() is None:
            return None

        (lat, lon) = self.first_position()
        return lat
        # Following will fail, if the very first Trackpoint ha no Position data (but th second)
        # if hasattr(self.activity.Lap.Track.Trackpoint, 'Position'):
        #     return self.activity.Lap.Track.Trackpoint.Position.LatitudeDegrees.pyval

    @property
    def longitude(self):
        """
        Returns the longitude from the first Position item
        :return: float or None, if no Position item found
        """
        if self.first_position() is None:
            return None

        (lat, lon) = self.first_position()
        return lon
        # Following will fail, if the very first Trackpoint ha no Position data (but th second)
        # if hasattr(self.activity.Lap.Track.Trackpoint, 'Position'):
        #     return self.activity.Lap.Track.Trackpoint.Position.LongitudeDegrees.pyval

    @property
    def activity_type(self):
        return self.activity.attrib['Sport'].lower()

    @property
    def started_at(self):
        """
        String in Z-format e.g. '2020-01-31T04:39:19.000Z'
        :return: Original datetime as String
        """
        return self.activity.Lap[0].attrib["StartTime"]

    @property
    def completed_at(self):
        return self.activity.Lap[-1].Track.Trackpoint[-1].Time.pyval

    @property
    def cadence_avg(self):
        return self.activity.Lap[-1].Cadence

    @property
    def distance(self):
        distance_values = self.distance_values()
        return distance_values[-1] if distance_values else 0

    @property
    def distance_units(self):
        return 'meters'

    @property
    def duration(self):
        """Returns duration of workout in seconds."""
        return sum(lap.TotalTimeSeconds for lap in self.activity.Lap)

    @property
    def calories(self):
        return sum(lap.Calories for lap in self.activity.Lap)

    @property
    def hr_avg(self):
        """Average heart rate of the workout"""
        hr_data = self.hr_values()
        
        if len(hr_data) == 0:
            return 0
        
        return int(sum(hr_data) / len(hr_data))

    @property
    def hr_max(self):
        """Maximum heart rate of the workout or None"""
        if len(self.hr_values()) == 0:
            return 0

        return max(self.hr_values())

    @property
    def hr_min(self):
        """Minimum heart rate of the workout"""
        return min(self.hr_values())

    @property
    def pace(self):
        """Average pace, formatted in mm:ss/km for the workout"""
        if self.distance > 0:
            secs_per_km = self.duration / (self.distance / 1000)
        else:
            secs_per_km = 0
        return time.strftime('%M:%S', time.gmtime(secs_per_km))

    @property
    def velocity_average(self):
        """Average velocity km/h for the workout"""
        return (self.distance / 1000.0) / (self.duration / 3600.0)

    @property
    def altitude_avg(self):
        """Average altitude for the workout"""
        altitude_data = self.altitude_points()
        return sum(altitude_data) / len(altitude_data)

    @property
    def altitude_max(self):
        """Max altitude for the workout"""
        altitude_data = self.altitude_points()
        return max(altitude_data, default=0)

    @property
    def altitude_min(self):
        """Min altitude for the workout"""
        altitude_data = self.altitude_points()
        return min(altitude_data, default=0)

    @property
    def has_altitude(self):
        return len(self.altitude_points()) > 0

    @property
    def ascent(self):
        """Returns ascent of workout in meters"""
        total_ascent = 0.0
        altitude_data = self.altitude_points()
        for i in range(len(altitude_data) - 1):
            diff = altitude_data[i+1] - altitude_data[i]
            if diff > 0.0:
                total_ascent += diff
        return total_ascent

    @property
    def descent(self):
        """Returns descent of workout in meters"""
        total_descent = 0.0
        altitude_data = self.altitude_points()
        for i in range(len(altitude_data) - 1):
            diff = altitude_data[i+1] - altitude_data[i]
            if diff < 0.0:
                total_descent += abs(diff)
        return total_descent

    @property
    def cadence_max(self):
        """Returns max cadence of workout"""
        cadence_data = self.cadence_values()
        return max(cadence_data)

    @property
    def activity_notes(self):
        """Return contents of Activity/Notes field if it exists."""
        return getattr(self.activity, 'Notes', '')
