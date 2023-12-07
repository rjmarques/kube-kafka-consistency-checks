from datetime import datetime

def millis_to_datetime(millis):
    # Convert milliseconds to seconds
    seconds = millis / 1000.0
    dt_object = datetime.fromtimestamp(seconds)
    return dt_object.strftime('%Y-%m-%d %H:%M:%S')