"""
Pass 1 of the Two-Pass Macro Processor.

Scans source code to identify macro definitions and builds:
  - MNT (Macro Name Table): [{name, mdt_index, params}]
  - MDT (Macro Definition Table): Model statements with positional markers (#1, #2, ...)
  - Intermediate Code: Non-macro lines passed through for Pass 2.
"""

RESERVED_KEYWORDS = {"MACRO", "MEND", "CALL", "PRINT", "SET"}


def _skip_to_mend(lines, i):
    """Advance index past the next MEND. Returns the new index."""
    i += 1
    while i < len(lines) and lines[i].strip() != "MEND":
        i += 1
    return i + 1  # skip the MEND itself


def pass1(lines):
    MNT = []
    MDT = []
    errors = []
    intermediate_lines = []
    defined_names = set()

    if not lines:
        errors.append("ERROR: Input is empty!")
        return intermediate_lines, MNT, MDT, errors

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if not line:
            i += 1
            continue

        tokens = line.split()

        if tokens[0] == "MACRO":
            # Error: MACRO with no name
            if len(tokens) < 2:
                errors.append(f"ERROR: Line {i+1} - MACRO keyword missing name")
                i = _skip_to_mend(lines, i)
                continue

            macro_name = tokens[1]
            params = tokens[2:]

            # Error: Reserved keyword as macro name
            if macro_name in RESERVED_KEYWORDS:
                errors.append(f"ERROR: Line {i+1} - '{macro_name}' is a reserved keyword")
                i = _skip_to_mend(lines, i)
                continue

            # Error: Duplicate macro definition
            if macro_name in defined_names:
                errors.append(f"ERROR: Line {i+1} - Duplicate macro definition '{macro_name}'")
                i = _skip_to_mend(lines, i)
                continue

            # Error: Duplicate formal parameters
            if len(set(params)) != len(params):
                errors.append(f"ERROR: Line {i+1} - Duplicate parameters in macro '{macro_name}'")

            # Error: Params not prefixed with &
            for p in params:
                if not p.startswith("&"):
                    errors.append(f"ERROR: Line {i+1} - Parameter '{p}' must start with '&'")

            # Record in MNT
            MNT.append({"name": macro_name, "mdt_index": len(MDT), "params": params})
            defined_names.add(macro_name)

            # Read macro body into MDT
            i += 1
            found_mend = False
            # Sort params by length (descending) once, to avoid &ab vs &a conflicts
            sorted_params = sorted(enumerate(params), key=lambda x: len(x[1]), reverse=True)

            while i < len(lines):
                body_line = lines[i].strip()

                if not body_line:
                    i += 1
                    continue

                if body_line == "MEND":
                    MDT.append("MEND")
                    found_mend = True
                    break

                # Error: Nested macro
                if body_line.split()[0] == "MACRO":
                    errors.append(f"ERROR: Line {i+1} - Nested macro definition is not allowed")
                    i = _skip_to_mend(lines, i)
                    continue

                # Replace formal parameters with positional markers #1, #2...
                model_stmt = body_line
                for idx, param in sorted_params:
                    model_stmt = model_stmt.replace(param, f"#{idx+1}")

                MDT.append(model_stmt)
                i += 1

            if not found_mend:
                errors.append(f"ERROR: Macro '{macro_name}' is missing MEND")

        elif tokens[0] == "MEND":
            errors.append(f"WARNING: Line {i+1} - MEND found outside of a macro definition")

        else:
            intermediate_lines.append(line)

        i += 1

    return intermediate_lines, MNT, MDT, errors