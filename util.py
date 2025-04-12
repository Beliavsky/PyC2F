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
    