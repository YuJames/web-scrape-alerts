# ~~~~  IMPORTS  ~~~~ #
from csv import (
    DictReader,
    QUOTE_ALL,
    writer
)
from io import (
    StringIO
)

from flatten_json import (
    flatten
)

# ~~~~  PRIVATE GLOBAL VARIABLES  ~~~~ #

# ~~~~  PUBLIC GLOBAL VARIABLES  ~~~~ #

# ~~~~  PRIVATE CLASSES  ~~~~ #

# ~~~~  PUBLIC CLASSES  ~~~~ #

# ~~~~  PRIVATE FUNCTIONS  ~~~~ #

# ~~~~  PUBLIC FUNCTIONS  ~~~~ #
def json_to_csv(data, reversed=False):
    """Convert json to csv.

    Args:
        data (object): json data
            (dict): json dict
            (list): json list
            (str): csv
        reversed (bool): conversion direction
            (True): csv to json
            (False): json to csv
    Returns:
        (object): converted data
            (dict): json dict
            (list): json list
            (str): csv
    """

    if not reversed:
        if isinstance(data, str): return data

        data = [data] if isinstance(data, dict) else data
        # flatten
        flat_obj = [flatten(x, separator="::") for x in data]
        # convert to csv
        csv_obj = StringIO()
        csv_writer = writer(csv_obj, quoting=QUOTE_ALL)
        col_headers = flat_obj[0].keys()
        csv_writer.writerow(col_headers)
        for row in flat_obj:
            csv_writer.writerow(row.values())
        result = csv_obj.getvalue()
    else:
        if isinstance(data, (dict, list)): return data

        json_obj = StringIO()
        json_obj.write(data)
        json_obj.seek(0)
        json_reader = DictReader(json_obj)
        result = [x for x in json_reader]
        
    return result

def order_object(data):
    """Recursively sort a json object.

    Args:
        data (object): json data
            (dict): json dict
            (list): json list
    Returns:
        (object): sorted json data
            (dict): json dict
            (list): json list
    """

    if isinstance(data, dict):
        result = {
            x: order_object(y) if isinstance(y, (list, dict)) else y
            for x, y in sorted(data.items())
        }
    elif isinstance(data, list):
        result = [
            order_object(x) if isinstance(x, (list, dict)) else x
            for x in sorted(data)
        ]
    
    return result

# ~~~~  DEAD CODE  ~~~~ #

