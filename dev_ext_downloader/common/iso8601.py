from datetime import datetime
from typing import Union

import pytz


class ISO8601ParseError(Exception):
    pass


def parse_iso8601(s: str, default_tz: Union[str, pytz.BaseTzInfo] = "UTC") -> datetime:
    s = s.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s)
    except ValueError as e:
        if "+" not in s and "-" not in s and "Z" not in s:
            try:
                dt = datetime.fromisoformat(s)
                default = _get_tz(default_tz)
                dt = default.localize(dt)
            except:
                raise ISO8601ParseError(f"Parse failed: {s}, error: {str(e)}") from e
        else:
            raise ISO8601ParseError(f"Parse failed: {s}, error: {str(e)}") from e
    if dt.tzinfo is None:
        default = _get_tz(default_tz)
        dt = default.localize(dt)
    return dt


def _get_tz(tz: Union[str, pytz.BaseTzInfo]) -> pytz.BaseTzInfo:
    if isinstance(tz, str):
        return pytz.timezone(tz)
    elif isinstance(tz, pytz.BaseTzInfo):
        return tz
    else:
        raise TypeError("default_tz must be str or pytz.BaseTzInfo")


def format_datetime(
        dt: datetime,
        target_tz: Union[str, pytz.BaseTzInfo] = "UTC",
        fmt: str = "%Y-%m-%d %H:%M:%S %Z%z",
) -> str:
    target = _get_tz(target_tz)
    dt_converted = dt.astimezone(target)
    return dt_converted.strftime(fmt)


def convert_tz(
        dt: datetime,
        from_tz: Union[str, pytz.BaseTzInfo],
        to_tz: Union[str, pytz.BaseTzInfo],
) -> datetime:
    from_tz_obj = _get_tz(from_tz)
    to_tz_obj = _get_tz(to_tz)

    if dt.tzinfo is None:
        dt = from_tz_obj.localize(dt)
    return dt.astimezone(to_tz_obj)


def get_utcnow() -> datetime:
    return datetime.now(pytz.utc)
