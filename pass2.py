"""
Pass 2 of the Two-Pass Macro Processor.

Scans intermediate code from Pass 1 and expands macro calls:
  - Looks up CALL targets in the MNT.
  - Builds a fresh ALA (Argument List Array) for each CALL.
  - Uses MDTP (MDT Pointer) to read and expand model statements from the MDT.
"""


def pass2(lines, MNT, MDT):
    output = []
    errors = []

    # Build lookup: macro_name -> MNT entry
    mnt_lookup = {entry["name"]: entry for entry in MNT}

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if not line:
            i += 1
            continue

        tokens = line.split()

        if tokens[0] == "CALL":
            # Error: CALL with no macro name
            if len(tokens) < 2:
                errors.append(f"ERROR: Line {i+1} - CALL missing macro name")
                i += 1
                continue

            macro_name = tokens[1]
            actual_args = tokens[2:]

            # Error: Undefined macro
            if macro_name not in mnt_lookup:
                errors.append(f"ERROR: Line {i+1} - Undefined macro '{macro_name}'")
                i += 1
                continue

            formal_params = mnt_lookup[macro_name]["params"]

            # Error: Argument count mismatch
            if len(actual_args) != len(formal_params):
                errors.append(
                    f"ERROR: Line {i+1} - Macro '{macro_name}' expects "
                    f"{len(formal_params)} arg(s), got {len(actual_args)}"
                )
                i += 1
                continue

            # Build ALA for this call: {#1: actual1, #2: actual2, ...}
            ALA = {f"#{idx+1}": arg for idx, arg in enumerate(actual_args)}

            # Expand using MDTP (MDT Pointer)
            mdtp = mnt_lookup[macro_name]["mdt_index"]
            while mdtp < len(MDT) and MDT[mdtp] != "MEND":
                expanded_line = MDT[mdtp]
                # Replace in reverse index order to avoid #1 matching inside #10
                for idx in range(len(actual_args), 0, -1):
                    expanded_line = expanded_line.replace(f"#{idx}", ALA[f"#{idx}"])
                output.append(expanded_line)
                mdtp += 1

        else:
            output.append(line)

        i += 1

    return output, errors