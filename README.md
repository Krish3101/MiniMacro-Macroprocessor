# Design of a Macroprocessor for MiniMacro

This project implements a two-pass macroprocessor designed for a user-defined, macro-based language called **MiniMacro**.

## Prerequisites

Install Python 3.8+ and the required GUI library:
```bash
pip install PyQt6
```

---

## 1. Language Constructs & Predefined Keywords
MiniMacro supports limited constructs, specifically utilizing the following **5 predefined keywords**:
1. `MACRO` — Signals the start of a macro definition
2. `MEND` — Signals the end of a macro definition
3. `CALL` — Used to invoke a previously defined macro
4. `PRINT` — A standard output operation
5. `SET` — Variable assignment keyword

*Note: The language uses space delimiters. Formal parameters inside macros are designated by the `&` prefix (e.g., `&a`, `&x`).*

---

## 2. Syntax: Definition and Invocation

### Macro Definition Syntax
```text
MACRO <MacroName> <&Param1> <&Param2> ...
    <Model Statement 1>
    <Model Statement 2>
    ...
MEND
```

### Macro Invocation Syntax
```text
CALL <MacroName> <Arg1> <Arg2> ...
```

---

## 3. Two-Pass Architecture Design

### Data Structures
| Structure | Purpose |
|-----------|---------|
| **MNT** (Macro Name Table) | Stores each macro's name, its starting index in the MDT, and the number of parameters. |
| **MDT** (Macro Definition Table) | Stores model statements of all macros sequentially. Formal parameters are replaced with positional index markers (`#1`, `#2`, ...). Each macro body ends with `MEND`. |
| **ALA** (Argument List Array) | A **temporary table** built fresh during each `CALL` in Pass 2. Maps positional markers (`#1`, `#2`) to the actual arguments provided. |

### Pass 1 — Definition Processing
1. Initialize MDTC (MDT Counter) = 0.
2. Scan source code line-by-line.
3. If `MACRO` is encountered:
   - Record name and MDTC in **MNT**.
   - Read body lines, replacing formal params with `#1`, `#2`, ... → store in **MDT**.
   - Store `MEND` as the last MDT entry for this macro.
4. If not a macro definition → write line to intermediate code.

### Pass 2 — Expansion
1. Read intermediate code from Pass 1.
2. For each line:
   - If it is a `CALL`: look up the macro in MNT, set MDTP (MDT Pointer) to the stored index, build a fresh **ALA** mapping `{#1: arg1, #2: arg2, ...}`, and expand each model statement by substituting markers with actual arguments.
   - Otherwise: pass the line through to the final output.

---

## 4. Demonstration of Macro Expansion

### Sample Input
```text
MACRO ADD_NUMS &a &b
    LOAD &a
    ADD &b
    STORE &a
MEND

MACRO DISPLAY &x
    PRINT &x
MEND

CALL ADD_NUMS 10 20
CALL DISPLAY 10
```

### Tables Built by Pass 1

**MNT:**
| Macro Name | MDT Index | #Params |
|------------|-----------|---------|
| ADD_NUMS   | 0         | 2       |
| DISPLAY    | 4         | 1       |

**MDT:**
| Index | Model Statement |
|-------|-----------------|
| 0     | LOAD #1         |
| 1     | ADD #2          |
| 2     | STORE #1        |
| 3     | MEND            |
| 4     | PRINT #1        |
| 5     | MEND            |

**ALA (built during `CALL ADD_NUMS 10 20`):**
| Marker | Actual Arg |
|--------|------------|
| #1     | 10         |
| #2     | 20         |

### Expanded Output
```text
LOAD 10
ADD 20
STORE 10
PRINT 10
```

---

## 5. Error Handling
The macroprocessor identifies and handles the following errors:

| # | Error | Pass | Example |
|---|-------|------|---------|
| 1 | Undefined Macro | Pass 2 | `CALL UNKNOWN_MACRO` |
| 2 | Incorrect Parameter Count | Pass 2 | `CALL ADD_NUMS 10` (expects 2, got 1) |
| 3 | Duplicate Macro Definition | Pass 1 | Defining `MACRO DUP` twice |
| 4 | Duplicate Formal Parameters | Pass 1 | `MACRO ADD &a &a` |
| 5 | Missing `MEND` | Pass 1 | File ends before `MEND` |
| 6 | Nested Macros | Pass 1 | `MACRO` inside another `MACRO` body |
| 7 | Invalid Parameter Prefix | Pass 1 | `MACRO ADD a b` (must use `&a &b`) |
| 8 | Reserved Keyword as Name | Pass 1 | `MACRO CALL &a` or `MACRO MEND &a` |
| 9 | Stray `MEND` | Pass 1 | `MEND` outside any macro definition |
| 10 | `MACRO` Missing Name | Pass 1 | Bare `MACRO` with no name |
| 11 | `CALL` Missing Name | Pass 2 | Bare `CALL` with no macro name |

---

## Project Structure
```
MiniMacro-Macroprocessor/
├── gui.py      # GUI application (PyQt6)
├── pass1.py    # Pass 1: Macro definition processing
├── pass2.py    # Pass 2: Macro expansion
└── README.md   # This file
```

## Usage
```bash
python3 gui.py
```
