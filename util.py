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
