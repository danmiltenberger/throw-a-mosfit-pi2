import csv
from dataclasses import fields
from pathlib import Path
from typing import Iterable
from classes import FieldState, Point


_POINT_FIELDS = {
    "our_bot_pos_in",
    "capture_zone_center",
    "their_bot_pos_in",
    "ball_pos_in",
}

_BOOL_FIELDS = {
    "ball_is_ours",
    "ball_is_theirs",
}

_STRING_FIELDS = {
    "our_bot_command",
}


def _fieldstate_csv_columns() -> list[str]:
    """Get CSV column names in dataclass field order."""
    columns = []

    for f in fields(FieldState):
        if f.name in _POINT_FIELDS:
            columns.extend([f"{f.name}_x", f"{f.name}_y"])
        else:
            columns.append(f.name)

    return columns


def save_fieldstates_to_csv(
    fieldstates: FieldState | Iterable[FieldState],
    filepath: str | Path,
) -> None:
    """Append one or more FieldStates to a CSV.

    Creates the file and writes the header if it is missing or empty.
    """
    filepath = Path(filepath)

    # Allow either a single FieldState or an iterable of FieldStates.
    if isinstance(fieldstates, FieldState):
        fieldstates = [fieldstates]

    write_header = not filepath.exists() or filepath.stat().st_size == 0

    with open(filepath, "a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=_fieldstate_csv_columns(),
        )

        if write_header:
            writer.writeheader()

        for state in fieldstates:
            row = {}

            for f in fields(FieldState):
                value = getattr(state, f.name)

                if f.name in _POINT_FIELDS:
                    row[f"{f.name}_x"] = value.x
                    row[f"{f.name}_y"] = value.y
                else:
                    row[f.name] = value

            writer.writerow(row)


def _parse_bool(value: str) -> bool:
    """Parse a Boolean without treating the string 'False' as True."""
    normalized = value.strip().lower()

    if normalized in {"true", "1"}:
        return True
    if normalized in {"false", "0"}:
        return False

    raise ValueError(f"Invalid Boolean value: {value!r}")


def load_fieldstates_from_csv(
    filepath: str | Path,
) -> list[FieldState]:
    """Load a CSV file into a list of FieldStates."""
    states = []

    with open(filepath, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        required_columns = set(_fieldstate_csv_columns())
        actual_columns = set(reader.fieldnames or [])
        missing_columns = required_columns - actual_columns

        if missing_columns:
            raise ValueError(
                "CSV is missing required columns: "
                + ", ".join(sorted(missing_columns))
            )

        for row_number, row in enumerate(reader, start=2):
            try:
                values = {}

                for f in fields(FieldState):
                    name = f.name

                    if name in _POINT_FIELDS:
                        values[name] = Point(
                            x=float(row[f"{name}_x"]),
                            y=float(row[f"{name}_y"]),
                        )
                    elif name in _BOOL_FIELDS:
                        values[name] = _parse_bool(row[name])
                    elif name in _STRING_FIELDS:
                        values[name] = row[name]
                    else:
                        values[name] = float(row[name])

                states.append(FieldState(**values))

            except (ValueError, TypeError, KeyError, AttributeError) as exc:
                raise ValueError(
                    f"Invalid FieldState in CSV record {row_number}: {exc}"
                ) from exc

    return states
