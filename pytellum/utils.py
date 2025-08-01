import logging
from dataclasses import make_dataclass
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

try:
    import colorlog  # type: ignore

    COLOR = True
except ImportError:
    COLOR = False

C_LOG_LEVEL = {
    "CRITICAL": 50,
    "ERROR": 40,
    "WARNING": 30,
    "INFO": 20,
    "DEBUG": 10,
    "NOTSET": 0,
}


def to_obj(data: Dict[str, Any], class_name: str = "DataClass"):
    """Convert nested dictionaries to nested dataclasses"""

    def get_field_type_and_process_value(value):
        if isinstance(value, dict):
            # Create nested dataclass
            nested_class = to_obj(value, f"Nested{class_name}")
            return type(nested_class), nested_class
        elif isinstance(value, list) and value and isinstance(value[0], dict):
            # List of dictionaries
            nested_class_type = type(to_obj(value[0], f"Nested{class_name}"))
            processed_list = [to_obj(item, f"Nested{class_name}") for item in value]
            return List[nested_class_type], processed_list
        else:
            return type(value), value

    field_definitions = []
    processed_data = {}

    for key, value in data.items():
        field_type, processed_value = get_field_type_and_process_value(value)
        field_definitions.append((key, field_type))
        processed_data[key] = processed_value

    DataClass = make_dataclass(class_name, field_definitions)
    return DataClass(**processed_data)


def iso_to_human(
    iso_string: str,
    format_type: Literal["full", "short", "date_only", "time_only", "relative"] = "full",
    timezone: Optional[str] = None,
) -> str:
    """
    Convert ISO 8601 string to human readable format with various options

    Args:
        iso_string: ISO 8601 formatted datetime string
        format_type: Type of formatting to apply
        timezone: Target timezone (e.g., 'US/Eastern', 'Europe/London')
    """
    # Parse the ISO string
    dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))

    # Convert timezone if specified
    if timezone:
        import pytz

        target_tz = pytz.timezone(timezone)
        dt = dt.astimezone(target_tz)

    # Format based on type
    if format_type == "full":
        return dt.strftime("%A, %B %d, %Y at %I:%M:%S %p %Z")
    elif format_type == "short":
        return dt.strftime("%m/%d/%Y %I:%M %p")
    elif format_type == "date_only":
        return dt.strftime("%B %d, %Y")
    elif format_type == "time_only":
        return dt.strftime("%I:%M %p")
    elif format_type == "relative":
        return get_relative_time(dt)
    else:
        return dt.strftime("%B %d, %Y at %I:%M %p")


def get_relative_time(dt: datetime) -> str:
    """Get relative time description (e.g., '2 hours ago', 'in 3 days')"""
    now = datetime.now(dt.tzinfo)
    diff = now - dt

    seconds = abs(diff.total_seconds())
    is_future = diff.total_seconds() < 0

    # Time units
    minute = 60
    hour = minute * 60
    day = hour * 24
    week = day * 7
    month = day * 30
    year = day * 365

    def format_relative(value: int, unit: str) -> str:
        plural = "s" if value != 1 else ""
        time_str = f"{value} {unit}{plural}"
        return f"in {time_str}" if is_future else f"{time_str} ago"

    if seconds < minute:
        return "just now"
    elif seconds < hour:
        return format_relative(int(seconds // minute), "minute")
    elif seconds < day:
        return format_relative(int(seconds // hour), "hour")
    elif seconds < week:
        return format_relative(int(seconds // day), "day")
    elif seconds < month:
        return format_relative(int(seconds // week), "week")
    elif seconds < year:
        return format_relative(int(seconds // month), "month")
    else:
        return format_relative(int(seconds // year), "year")


def console_logger(name, level="DEBUG"):  # sourcery skip: avoid-builtin-shadow
    """
    This method create an instance of python logging and sets the following format for log messages.
        <date> <time> - <name> - <level> - <message>

    :param name: String displayed after data and time. Define it to identify\
        from which part of the code, log message is generated.
    :type name: str
    :param level: Logging level to display messages from a certain level, defaults to "DEBUG".
    :type level: str, optional
    :return: An instance of the logging.Logger class.
    :rtype: logging.Logger
    """
    channel_handler = logging.StreamHandler()
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    f = format
    if COLOR:
        cformat = f"%(log_color)s{format}"
        f = colorlog.ColoredFormatter(
            cformat,
            date_format,
            log_colors={
                "DEBUG": "bold_cyan",
                "INFO": "blue",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            },
        )
    else:
        f = logging.Formatter(format, date_format)
    channel_handler.setFormatter(f)

    logger = logging.getLogger(name)
    logger.setLevel(C_LOG_LEVEL[level])
    logger.addHandler(channel_handler)

    return logger
