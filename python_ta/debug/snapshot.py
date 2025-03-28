"""
Use the 'inspect' module to extract local variables from
 multiple stack frames. Useful for dynamic debugging.
"""

from __future__ import annotations

import inspect
from types import FrameType
from typing import Any


def get_filtered_global_variables(frame: FrameType) -> dict:
    """
    Helper function for retriving global variables
    (i.e. top level variables in "__main__" frame's scope)
    excluding, certain types (types of data that is
    irrelevant in an intro level to Python programming language).
    """
    global_vars = frame.f_globals
    true_global_vars = {
        var: global_vars[var]
        for var in global_vars
        if not var.startswith("__")
        and not inspect.ismodule(global_vars[var])
        and not inspect.isfunction(global_vars[var])
        and not inspect.isclass(global_vars[var])
    }
    return {"__main__": true_global_vars}


def snapshot():
    """Capture a snapshot of local variables from the current and outer stack frames
    where the 'snapshot' function is called. Returns a list of dictionaries,
    each mapping function names to their respective local variables.
    Excludes the global module context.
    """
    variables = []
    frame = inspect.currentframe().f_back

    while frame:
        if frame.f_code.co_name != "<module>":
            variables.append({frame.f_code.co_name: frame.f_locals})
        else:
            global_vars = get_filtered_global_variables(frame)
            variables.append(global_vars)

        frame = frame.f_back

    return variables


def snapshot_to_json(snapshot_data: list[dict]) -> list[dict]:
    """
    Convert the snapshot data into a simplified JSON format, where each value
    has its own entry with a matching ID. This includes nesting the process_value
    function to handle recursive processing of data types.
    """

    json_data = []  # This will store the converted frames and their variables
    value_entries = []  # Stores additional processed value entries
    global_ids = {}  # Maps values to their unique IDs
    id_counter = 1  # Using an int for a mutable reference

    def process_value(val: Any) -> int:
        """
        Recursively processes a value, handling compound built-in data types
        (lists, sets, tuples, and dicts) by creating a list or dict of IDs for their elements.
        This process assigns a unique ID to the input value. This ID, which uniquely identifies
        the processed value in a global context, is returned by the function. The returned ID
        ensures that each value is processed only once, facilitating the reconstruction of
        the original data structure with its elements uniquely identified.

        """
        nonlocal id_counter  # This allows us to modify id_counter directly
        nonlocal global_ids, value_entries
        value_id = id(val)
        if value_id not in global_ids:
            global_ids[value_id] = id_counter
            value_id_diagram = id_counter
            id_counter += 1  # Now directly incrementing the integer

            if isinstance(val, (list, set, tuple)):
                element_ids = [process_value(element) for element in val]
                value_entry = {
                    "isClass": False,
                    "name": type(val).__name__,
                    "id": value_id_diagram,
                    "value": element_ids,
                }
            elif isinstance(val, dict):
                dict_ids = {}
                for key, v in val.items():
                    key_id = process_value(key)
                    val_id = process_value(v)
                    dict_ids[key_id] = val_id
                value_entry = {
                    "isClass": False,
                    "name": "dict",
                    "id": value_id_diagram,
                    "value": dict_ids,
                }
            else:
                value_entry = {
                    "isClass": False,
                    "name": type(val).__name__,
                    "id": value_id_diagram,
                    "value": val,
                }

            value_entries.append(value_entry)
        else:
            value_id_diagram = global_ids[value_id]

        return value_id_diagram

    for frame in snapshot_data:
        frame_variables = {}
        for frame_name, frame_data in frame.items():
            for var_name, value in frame_data.items():
                var_id_diagram = process_value(value)
                frame_variables[var_name] = var_id_diagram

            json_object_frame = {
                "isClass": True,
                "name": frame_name,
                "id": None,
                "value": frame_variables,
                "stack_frame": True,
            }
            json_data.append(json_object_frame)

    json_data.extend(value_entries)
    return json_data
