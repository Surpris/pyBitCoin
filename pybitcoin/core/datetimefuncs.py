#-*- coding: utf-8 -*-
import datetime
import numpy as np

def is_weekend(dt):
    """
    Judge whether the day is weekend.
    Here `weekend` correspoonds to the range from 06:00:00 on Saturday to 06:00:00 on Monday.
    """
    if dt.weekday() == 5:
        return dt.hour >= 6
    elif dt.weekday() == 6:
        return True
    elif dt.weekday() == 0:
        return dt.hour < 6
    else:
        return False

def datetime2timeInteger(dt):
    """
    Convert a datetime object `dt` to the integer "YYYYmmddHHMMSS".
    """
    return int("{0}{1:02d}{2:02d}{3:02d}{4:02d}{5:02d}".\
               format(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second))

def datetime2time(dt, unit="sec"):
    """
    Convert a datetime object `dt` to the value in the unit `unit`.
    <remark>
        This method may cause `RuntimeWarning: overflow encountered in long_scalars`
        if `dt.year` is very large (>~ 100), so it is recommended that the method
        `_datetime2time2()` should be used instead.
    </remark>
    """
    def month2days(dt2):
        if dt2.month == 1:
            return 0
        else:
            if dt2.year % 4 == 0 and dt2.year % 100 != 0:
                month2 = 29
            else:
                month2 = 28
            days = [31, month2, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
            return sum(days[0:dt2.month])
    def year2days(dt2):
        years = np.arange(1, dt2.year+0.5, 1, dtype=int)
        leaps = sum((years % 4 == 0)&(years % 100 != 0)&(years!=years[-1]))
        return 366*leaps + 365*(len(years)-1-leaps)

    if not isinstance(dt, datetime.datetime):
        raise TypeError
    units = ["sec", "min", "hour", "day", "month", "year"]
    dt_val = np.array([dt.second, dt.minute, dt.hour, dt.day, dt.month, dt.year], dtype=int)
    units_val = np.array([1, 60, 3600, 24*3600, month2days(dt)*24*2600, year2days(dt)*24*3600], dtype=int)
    total_sec = sum(dt_val*units_val) - 86400 # Subtract the value corresponding to "0001/01/01 00:00:00".
    if unit not in units:
        raise ValueError("unit must be in [" + ",".join(units) + "]")
    elif unit == "sec":
        return total_sec
    else:
        return float(total_sec) / float(units_val[units.index(unit)])
