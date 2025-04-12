def remove_newlines_in_quotes(text):
    """Remove literal '\n' sequences within single- or
    double-quoted text in a string, preserving '\n' outside quotes."""
    result = []
    i = 0
    in_quote = False
    quote_char = None
    
    while i < len(text):
        if text[i] in ('"', "'") and (i == 0 or text[i-1] != '\\'):
            # Toggle quote state
            if in_quote and text[i] == quote_char:
                in_quote = False
                quote_char = None
            elif not in_quote:
                in_quote = True
                quote_char = text[i]
            result.append(text[i])
            i += 1
        elif in_quote and text[i] == '\\' and i + 1 < len(text) and text[i + 1] == 'n':
            # Skip \n inside quotes
            i += 2
        else:
            # Copy character as is
            result.append(text[i])
            i += 1
    return ''.join(result)

def get_before_inc_dec(line):
    """Extracts the substring before '++' or '--' and identifies the operator.
    
    Args:
        line (str): Input string to process.
        
    Returns:
        tuple: (substring before '++' or '--' or '', operator '++', '--', or '').
    """
    pos_plus = line.find('++')
    pos_minus = line.find('--')
    
    if pos_plus == -1 and pos_minus == -1:
        return ("", "")
    
    if pos_plus != -1 and (pos_minus == -1 or pos_plus < pos_minus):
        return (line[:pos_plus].strip(), "++")
    else:
        return (line[:pos_minus].strip(), "--")

def remove_blank_lines(text):
    """Remove blank lines from a multiline string.
    
    Args:
        text (str): Input multiline string.
        
    Returns:
        str: String with blank lines removed.
    """
    return '\n'.join(line for line in text.splitlines() if line.strip())

def process_segment(segment_lines: list) -> list:
    """
    Given a list of lines for a block (or global code) that does not contain nested blocks,
    this function moves any declaration line (i.e. one containing "::" and not a full comment)
    to immediately after the header of the block. For functions and subroutines the header
    is taken as the initial lines up to (and including) the line with "implicit none".
    For other blocks a slightly different heuristic is used.
    """
    declaration_lines = []
    other_lines = []
    for line in segment_lines:
        stripped = line.strip()
        if "::" in line and not stripped.startswith("!"):
            declaration_lines.append(line)
        else:
            other_lines.append(line)

    # Determine if this segment is a function or subroutine.
    seg_header = None
    for line in other_lines:
        if line.strip() == "" or line.strip().startswith("!"):
            continue
        seg_header = line.strip().lower()
        break

    insertion_index = None
    if seg_header is not None and (seg_header.startswith("function") or seg_header.startswith("subroutine")):
        # For functions/subroutines, we insert immediately after "implicit none" (if present).
        for idx, line in enumerate(other_lines):
            if "implicit none" in line.lower():
                insertion_index = idx + 1
                break
        if insertion_index is None:
            insertion_index = 1 if other_lines else 0
    else:
        # For other blocks, use the previous heuristic:
        for idx, line in enumerate(other_lines):
            if "implicit none" in line.lower():
                insertion_index = idx + 1
                # Preserve any following blank line.
                for j in range(idx + 1, len(other_lines)):
                    if other_lines[j].strip() == "":
                        insertion_index = j + 1
                        break
                break
        if insertion_index is None:
            if other_lines:
                first = other_lines[0].lstrip().lower()
                if any(first.startswith(kw) for kw in ("program", "module", "function", "subroutine")):
                    insertion_index = 1
                else:
                    insertion_index = 0
            else:
                insertion_index = 0

    return other_lines[:insertion_index] + declaration_lines + other_lines[insertion_index:]


def is_block_start(line: str) -> bool:
    """Return True if a line (non-comment) starts a block (module, program, subroutine, or function)."""
    stripped = line.lstrip()
    if not stripped or stripped.startswith("!"):
        return False
    low = stripped.lower()
    # Do not treat lines starting with "end" as block starters.
    if low.startswith("end"):
        return False
    for kw in ("module", "program", "subroutine", "function"):
        if low.startswith(kw):
            return True
    return False


def is_module_line(line: str) -> bool:
    """
    Return True if a line (non-comment) starts a module block.
    (Excludes lines like "module procedure" which belong inside modules.)
    """
    stripped = line.lstrip()
    if not stripped or stripped.startswith("!"):
        return False
    low = stripped.lower()
    return low.startswith("module") and "module procedure" not in low


def is_procedure_start(line: str) -> bool:
    """Return True if a line starts a subroutine or function block."""
    stripped = line.lstrip().lower()
    return stripped.startswith("subroutine") or stripped.startswith("function")


def extract_block(lines: list, start_index: int) -> (list, int):
    """
    Extract a block starting at start_index (assumed to be a block start) until
    the first line that starts with "end" (case-insensitive). Returns the block
    as a list of lines and the index of the next line after the block.
    """
    block = [lines[start_index]]
    i = start_index + 1
    while i < len(lines):
        block.append(lines[i])
        if lines[i].lstrip().lower().startswith("end"):
            i += 1
            break
        i += 1
    return block, i


def process_module_block(module_block: list) -> list:
    """
    Process a module block. If the module has a CONTAINS section, the block is split
    into a header (up to and including the "contains" line) and a body.
    Each procedure in the body is extracted and processed individually so that
    its declarations remain within the procedure.
    """
    contains_index = None
    for idx, line in enumerate(module_block):
        if line.lstrip().lower().startswith("contains"):
            contains_index = idx
            break
    if contains_index is not None:
        header_part = process_segment(module_block[:contains_index])
        contains_line = module_block[contains_index]
        body_part = module_block[contains_index+1:-1]
        end_line = module_block[-1]
        processed_body = []
        i = 0
        while i < len(body_part):
            if is_procedure_start(body_part[i]):
                proc_block, i = extract_block(body_part, i)
                processed_proc = process_segment(proc_block)
                processed_body.extend(processed_proc)
            else:
                processed_body.append(body_part[i])
                i += 1
        return header_part + [contains_line] + processed_body + [end_line]
    else:
        return process_segment(module_block)


def move_declarations_to_top(fortran_code: str) -> str:
    """
    Rearranges Fortran code so that any lines containing declarations
    (indicated by the occurrence of "::") are moved to the beginning of the
    block (global or within a function/subroutine/module/program), without moving
    declarations out of their containing procedure.

    Blocks are assumed to start with a non-comment line containing one of the keywords:
    "module", "program", "subroutine", or "function" (case-insensitive), and end at the first line
    starting with "end" (case-insensitive). In modules with a CONTAINS section,
    the procedures following CONTAINS are processed separately.

    Parameters:
        fortran_code (str): The original Fortran source code as a multiline string.

    Returns:
        str: The modified Fortran code with declaration lines moved within their blocks.
    """
    lines = fortran_code.splitlines()
    result_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if is_module_line(line):
            module_block, i = extract_block(lines, i)
            processed_module = process_module_block(module_block)
            result_lines.extend(processed_module)
        elif is_block_start(line):
            block, i = extract_block(lines, i)
            processed_block = process_segment(block)
            result_lines.extend(processed_block)
        else:
            result_lines.append(line)
            i += 1
    return "\n".join(result_lines)
