#!/usr/bin/env python3
"""
Main translator class for converting C code to Fortran.
"""

import re

class CToFortranTranslator:
    def __init__(self):
        self.variables = set()
        self.functions = {}
        self.current_function = None
        self.indent_level = 0
        self.indent_str = "  "  # Two spaces for indentation
        # Track variable declarations for proper array handling
        self.variable_types = {}

    def indent(self):
        """Return the current indentation string."""
        return self.indent_str * self.indent_level

    def translate_file(self, input_file, output_file):
        """Translate a C file to Fortran."""
        try:
            with open(input_file, 'r') as f:
                c_code = f.read()
            
            fortran_code = self.translate_code(c_code)
            
            with open(output_file, 'w') as f:
                f.write(fortran_code)
                
            print(f"Translation complete. Output written to {output_file}")
            return True
        except Exception as e:
            print(f"Error during translation: {str(e)}")
            raise

    def translate_code(self, c_code):
        """Translate C code to Fortran."""
        # Preprocess: remove preprocessor directives
        c_code = self.remove_preprocessor_directives(c_code)
        
        # Extract functions and translate them
        c_functions = self.extract_functions(c_code)
        
        # Start with program header
        fortran_code = "! Translated from C to Fortran\n"
        fortran_code += "program main\n"
        fortran_code += "  implicit none\n\n"
        
        # Add main function body
        if "main" in c_functions:
            main_body = c_functions.pop("main")  # Remove main from functions dict
            self.current_function = "main"
            
            # Translate main function body
            translated_body = self.translate_function_body_iterative(main_body, is_main=True)
            fortran_code += translated_body
            fortran_code += "\nend program main\n\n"
        else:
            fortran_code += "  ! No main function found\n"
            fortran_code += "end program main\n\n"
        
        # Add function implementations after the main program
        for func_name, func_body in c_functions.items():
            self.current_function = func_name
            func_info = self.functions[func_name]
            return_type = func_info["return_type"]
            params = func_info["params"]
            
            fortran_type = self.translate_type(return_type)
            
            # Function or subroutine?
            if fortran_type.lower() == "void":
                fortran_code += f"subroutine {func_name}("
            else:
                fortran_code += f"function {func_name}("
            
            # Translate parameters
            param_list = []
            for param in params:
                param_name = param.split()[-1].replace("*", "").replace("&", "")
                param_list.append(param_name)
            
            fortran_code += ", ".join(param_list)
            
            if fortran_type.lower() == "void":
                fortran_code += ")\n"
            else:
                fortran_code += f") result({func_name}_result)\n"
            
            fortran_code += "  implicit none\n"
            
            # Declare parameters
            for param in params:
                param_parts = param.split()
                param_type = " ".join(param_parts[:-1])
                param_name = param_parts[-1].replace("*", "").replace("&", "")
                
                fortran_type_param = self.translate_type(param_type)
                fortran_code += f"  {fortran_type_param}, intent(in) :: {param_name}\n"
            
            # Declare return value if not void
            if fortran_type.lower() != "void":
                fortran_code += f"  {fortran_type} :: {func_name}_result\n"
            
            # Translate function body
            translated_body = self.translate_function_body_iterative(func_body)
            fortran_code += translated_body
            
            if fortran_type.lower() == "void":
                fortran_code += f"end subroutine {func_name}\n\n"
            else:
                fortran_code += f"end function {func_name}\n\n"
        
        return fortran_code

    def translate_type(self, c_type):
        """Translate C type to Fortran type."""
        c_type = c_type.lower()
        
        if 'int' in c_type:
            return "integer"
        elif 'unsigned' in c_type and ('int' in c_type or 'long' in c_type):
            return "integer"  # Fortran doesn't have unsigned types
        elif 'long' in c_type and 'long' in c_type:
            return "integer(kind=8)"  # long long is 64-bit
        elif 'long' in c_type:
            return "integer(kind=4)"  # long is typically 32-bit
        elif 'float' in c_type:
            return "real"
        elif 'double' in c_type:
            return "double precision"  # or real(kind=8)
        elif 'char' in c_type and '*' in c_type:
            return "character(len=100)"  # Arbitrary length - can be adjusted
        elif 'char' in c_type:
            return "character"
        elif 'bool' in c_type:
            return "logical"
        elif 'void' in c_type:
            return "void"  # Will be handled specially
        else:
            return "! Unknown type: " + c_type

    def remove_preprocessor_directives(self, c_code):
        """Remove preprocessor directives from C code."""
        lines = c_code.split('\n')
        filtered_lines = []
        
        for line in lines:
            stripped = line.strip()
            if not stripped.startswith('#'):
                filtered_lines.append(line)
            else:
                # Add a comment to preserve information about includes
                if stripped.startswith('#include'):
                    filtered_lines.append(f"! {stripped}")
        
        return '\n'.join(filtered_lines)

    def extract_functions(self, c_code):
        """Extract function definitions from C code."""
        # Regular expression to match function definitions
        func_pattern = r'(\w+)\s+(\w+)\s*\((.*?)\)\s*\{((?:[^{}]|(?:\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\}))*\}))*\}))*)\}'
        
        functions = {}
        for match in re.finditer(func_pattern, c_code, re.DOTALL):
            return_type = match.group(1)
            func_name = match.group(2)
            params_str = match.group(3).strip()
            body = match.group(4)
            
            # Parse parameters
            params = []
            if params_str and params_str.lower() != "void":
                for param in params_str.split(','):
                    param = param.strip()
                    if param:
                        params.append(param)
            
            # Store function info
            self.functions[func_name] = {
                "return_type": return_type,
                "params": params
            }
            
            functions[func_name] = body
        
        return functions

    def collect_declarations(self, c_body):
        """
        Collect variable declarations from C code.
        Return a dictionary mapping variable names to their types and array status.
        """
        declarations = {}
        c_lines = c_body.split('\n')
        
        for line in c_lines:
            line = line.strip()
            if self.is_declaration(line):
                # Extract type and variable name
                line = line.rstrip(';')
                
                # Handle array declarations
                if '[' in line or '{' in line:
                    # This is an array declaration
                    array_init = None
                    if '{' in line:
                        # Array with initialization
                        array_init = line[line.find('{'):line.rfind('}')+1]
                        line = line[:line.find('{')] + line[line.rfind('}')+1:]
                    
                    # Extract variable name
                    parts = line.split()
                    if len(parts) >= 2:
                        var_type = parts[0]
                        var_name = parts[1].split('[')[0].strip()
                        
                        # Store the variable info
                        declarations[var_name] = (var_type, True, array_init)
                        self.variable_types[var_name] = (var_type, True)
                else:
                    # Simple variable declaration
                    if '=' in line:
                        parts = line.split('=', 1)
                        declaration = parts[0].strip()
                    else:
                        declaration = line
                    
                    parts = declaration.split()
                    if len(parts) >= 2:
                        var_type = parts[0]
                        var_name = parts[1].strip()
                        
                        # Store the variable info
                        declarations[var_name] = (var_type, False, None)
                        self.variable_types[var_name] = (var_type, False)
        
        return declarations
    
    def is_declaration(self, line):
        """Check if a line is a variable declaration."""
        line = line.strip()
        if not line or not line.endswith(';'):
            return False
        
        # Check for common types
        return (
            line.startswith('int ') or 
            line.startswith('float ') or 
            line.startswith('double ') or 
            line.startswith('char ') or
            line.startswith('long ')
        )
    
    def translate_for_loop_start(self, init, condition, increment):
        """Translate the start of a C for loop to Fortran."""
        fortran_loop = ""
        
        # Check for variable declaration in loop
        init_var_decl = None
        if ' ' in init and '=' in init:
            # Declaration with initialization, e.g., "int i = 0"
            parts = init.split('=', 1)
            decl_parts = parts[0].strip().split()
            if len(decl_parts) >= 2:
                var_type = decl_parts[0]
                var_name = decl_parts[1].strip()
                start_val = parts[1].strip()
                
                # Add the declaration before the loop
                fortran_type = self.translate_type(var_type)
                init_var_decl = f"{fortran_type} :: {var_name}\n"
                
                # Update for the regular for loop processing
                init = f"{var_name}={start_val}"
        
        # Parse initialization
        init_parts = init.split('=')
        if len(init_parts) == 2:
            loop_var = init_parts[0].strip()
            start_val = init_parts[1].strip()
        else:
            # Can't parse initialization
            return self.indent() + f"! Failed to parse for loop: for ({init}; {condition}; {increment})\n"
        
        # Parse condition
        cond_parts = re.split(r'<=|<|>=|>|!=|==', condition)
        if len(cond_parts) == 2:
            cond_var = cond_parts[0].strip()
            end_var = cond_parts[1].strip()
            
            # Extract comparison operator
            if '<=' in condition:
                # i <= n becomes i = 1, n in Fortran
                pass
            elif '<' in condition:
                # i < n becomes i = 1, n-1 in Fortran
                end_var = f"{end_var} - 1"
            elif '>=' in condition:
                # Reverse loop
                tmp = start_val
                start_val = end_var
                end_var = tmp
            elif '>' in condition:
                # Reverse loop
                tmp = start_val
                start_val = end_var
                end_var = f"{end_var} + 1"
        else:
            # Can't parse condition
            return self.indent() + f"! Failed to parse for loop condition: {condition}\n"
        
        # Parse increment
        step = "1"
        if '+=' in increment:
            inc_parts = increment.split('+=') 
            step = inc_parts[1].strip()
        elif '-=' in increment:
            inc_parts = increment.split('-=')
            step = f"-{inc_parts[1].strip()}"
        elif '++' in increment:
            step = "1"
        elif '--' in increment:
            step = "-1"
        elif '=' in increment and '+' in increment.split('=')[1]:
            inc_parts = increment.split('=')
            if '+' in inc_parts[1]:
                add_parts = inc_parts[1].split('+')
                step = add_parts[1].strip()
        elif '=' in increment and '-' in increment.split('=')[1]:
            inc_parts = increment.split('=')
            if '-' in inc_parts[1]:
                sub_parts = inc_parts[1].split('-')
                step = f"-{sub_parts[1].strip()}"
        
        # Add any variable declaration first
        if init_var_decl:
            fortran_loop += self.indent() + init_var_decl
        
        # Build Fortran do loop
        fortran_loop += self.indent() + f"do {loop_var.strip()} = {start_val}, {end_var}"
        if step != "1":
            fortran_loop += f", {step}"
        fortran_loop += "\n"
        
        return fortran_loop
    
    def translate_for_loop_end(self):
        """Translate the end of a C for loop to Fortran."""
        return self.indent() + "end do\n"
    
    def translate_while_loop_start(self, condition):
        """Translate the start of a C while loop to Fortran."""
        # Translate condition
        fortran_condition = self.translate_expression(condition)
        
        # Build Fortran while loop (using do-while construct)
        return self.indent() + "do while (" + fortran_condition + ")\n"
    
    def translate_while_loop_end(self):
        """Translate the end of a C while loop to Fortran."""
        return self.indent() + "end do\n"
    
    def translate_if_start(self, condition):
        """Translate the start of a C if statement to Fortran."""
        # Translate condition
        fortran_condition = self.translate_expression(condition)
        
        # Build Fortran if statement
        return self.indent() + "if (" + fortran_condition + ") then\n"
    
    def translate_if_end(self):
        """Translate the end of a C if statement to Fortran."""
        return self.indent() + "end if\n"
    
    def translate_else_if(self, condition):
        """Translate a C else if statement to Fortran."""
        # Translate condition
        fortran_condition = self.translate_expression(condition)
        
        # Build Fortran else if statement
        return self.indent() + "else if (" + fortran_condition + ") then\n"
    
    def translate_else(self):
        """Translate a C else statement to Fortran."""
        return self.indent() + "else\n"

    def translate_declaration(self, c_declaration):
        """Translate a C variable declaration to Fortran."""
        # Remove semicolon
        c_declaration = c_declaration.rstrip(';')
        
        # Check for assignment
        if '=' in c_declaration:
            parts = c_declaration.split('=', 1)
            declaration = parts[0].strip()
            value = parts[1].strip()
        else:
            declaration = c_declaration
            value = None
        
        # Parse declaration parts
        parts = declaration.split()
        if len(parts) < 2:
            return self.indent() + f"! Failed to parse declaration: {c_declaration}\n"
        
        c_type = parts[0]
        var_name = parts[1]
        
        # Handle array declarations
        if '[' in var_name or (value and '{' in value):
            # This is an array declaration
            var_name = var_name.split('[')[0].strip()
            
            # Add to variables set
            self.variables.add(var_name)
            
            # Translate type
            fortran_type = self.translate_type(c_type)
            
            # Parse array dimensions or initialization
            if value and '{' in value:
                # Array with initialization
                elements = re.search(r'\{(.*?)\}', value).group(1)
                elements = [e.strip() for e in elements.split(',')]
                size = len(elements)
                
                # Build Fortran declaration
                fortran_decl = self.indent() + f"{fortran_type}, dimension({size}) :: {var_name} = [{', '.join(elements)}]"
            else:
                # Array without initialization or with size only
                if '[' in var_name:
                    size_match = re.search(r'\[(.*?)\]', var_name)
                    if size_match and size_match.group(1).strip():
                        size = size_match.group(1).strip()
                        fortran_decl = self.indent() + f"{fortran_type}, dimension({size}) :: {var_name}"
                    else:
                        fortran_decl = self.indent() + f"{fortran_type}, dimension(:) :: {var_name}"
                else:
                    fortran_decl = self.indent() + f"{fortran_type}, dimension(:) :: {var_name}"
        else:
            # Add to variables set
            self.variables.add(var_name)
            
            # Translate type
            fortran_type = self.translate_type(c_type)
            
            # Build Fortran declaration
            fortran_decl = self.indent() + f"{fortran_type} :: {var_name}"
            
            # Add initialization if present
            if value:
                fortran_decl += f" = {self.translate_expression(value)}"
        
        return fortran_decl + "\n"

    def translate_printf(self, c_printf):
        """Translate a C printf statement to Fortran using list-directed formatting."""
        # Remove semicolon
        c_printf = c_printf.rstrip(';')
        
        # Extract printf arguments
        printf_match = re.match(r'printf\s*\(\s*"(.*?)"\s*(,\s*(.*))?\s*\)', c_printf)
        if not printf_match:
            return self.indent() + f"! Failed to parse printf: {c_printf}\n"
        
        # In this simplified translation we ignore the format string
        args = printf_match.group(3) if printf_match.group(3) else ""
        fortran_print = self.indent() + "print*,"
        
        if args:
            arg_list = args.split(',')
            translated_args = [self.translate_expression(arg.strip()) for arg in arg_list]
            fortran_print += " " + ", ".join(translated_args)
        else:
            # If no arguments, output the literal from the format string if any
            literal = printf_match.group(1)
            if literal:
                fortran_print += " " + f'"{literal}"'
            else:
                fortran_print += " "
        
        return fortran_print + "\n"
    
    def translate_scanf(self, c_scanf):
        """Translate a C scanf statement to Fortran read statement."""
        # Remove semicolon
        c_scanf = c_scanf.rstrip(';')
        
        # Extract scanf arguments
        scanf_match = re.match(r'scanf\s*\(\s*"([^"]*)"\s*(,\s*(.*))?\s*\)', c_scanf)
        if not scanf_match:
            return self.indent() + f"! Failed to parse scanf: {c_scanf}\n"
        
        format_str = scanf_match.group(1)
        args = scanf_match.group(3) if scanf_match.group(3) else ""
        
        # Parse arguments - these are pointers to variables in C
        var_list = []
        if args:
            for arg in args.split(','):
                arg = arg.strip()
                if arg.startswith('&'):
                    var_list.append(arg[1:])  # Remove & from variable name
                else:
                    var_list.append(arg)
        
        # Build Fortran read statement
        fortran_read = self.indent() + "read(*, *"
        
        # Add error handling
        fortran_read += ", iostat=result) "
        
        # Add variable list
        fortran_read += ", ".join(var_list)
        
        # Add error check for read
        fortran_read += "\n" + self.indent() + "if (result /= 0) then\n"
        fortran_read += self.indent() + "  ! Handle read error\n"
        fortran_read += self.indent() + "end if\n"
        
        return fortran_read
    
    def get_var_type(self, var_name):
        """Get the type of a variable if it's known."""
        if var_name in self.variable_types:
            return self.variable_types[var_name][0]
        return "unknown"

    def translate_expression(self, c_expr):
        """Translate a C expression to Fortran - Using string replacements to avoid recursion."""
        if not c_expr:
            return c_expr
            
        # Replace C logical operators with Fortran ones
        fortran_expr = c_expr
        
        # Replace C specific constants
        fortran_expr = fortran_expr.replace('INT_MAX', 'huge(0)')
        fortran_expr = fortran_expr.replace('INT_MIN', '-huge(0)')
        fortran_expr = fortran_expr.replace('LONG_MAX', 'huge(0)')
        fortran_expr = fortran_expr.replace('NULL', 'null()')
        
        # Handle C array access with [] to Fortran ()
        if '[' in fortran_expr and ']' in fortran_expr:
            # This is a basic implementation - a more robust version would use a parser
            array_pattern = r'(\w+)\s*\[([^]]+)\]'
            while re.search(array_pattern, fortran_expr):
                fortran_expr = re.sub(array_pattern, r'\1(\2+1)', fortran_expr)  # Add 1 for 1-based indexing
        
        # Handle array initialization
        if '{' in fortran_expr and '}' in fortran_expr:
            # Convert {1, 2, 3} to [1, 2, 3]
            array_init_pattern = r'\{([^{}]*)\}'
            fortran_expr = re.sub(array_init_pattern, r'[\1]', fortran_expr)
        
        # Simple string replacements to avoid recursion issues
        # Order matters - do the longer patterns first
        
        # Comparison operators
        fortran_expr = fortran_expr.replace('==', ' == ')  # Add spaces to avoid issues
        fortran_expr = fortran_expr.replace('!=', ' /= ')
        fortran_expr = fortran_expr.replace('>=', ' >= ')
        fortran_expr = fortran_expr.replace('<=', ' <= ')
        fortran_expr = fortran_expr.replace('>', ' > ')
        fortran_expr = fortran_expr.replace('<', ' < ')
        
        # Logical operators
        fortran_expr = fortran_expr.replace('&&', ' .and. ')
        fortran_expr = fortran_expr.replace('||', ' .or. ')
        
        # "not" is tricky - we need to avoid replacing the "!" in other contexts
        if fortran_expr.strip().startswith('!'):
            fortran_expr = '.not.' + fortran_expr.strip()[1:]
        
        # Handle sizeof() which doesn't exist in Fortran
        sizeof_pattern = r'sizeof\s*\(\s*(\w+)\s*\)'
        if re.search(sizeof_pattern, fortran_expr):
            # Replace with kind-specific byte size
            fortran_expr = re.sub(sizeof_pattern, r'kind(0)', fortran_expr)  # Simplified
        
        return fortran_expr

    def translate_function_body_iterative(self, c_body, is_main=False):
        """
        Translate C function body to Fortran using an iterative approach.
        This avoids recursion depth issues with nested statements.
        """
        fortran_body = ""
        
        # Collect variable declarations
        declarations = self.collect_declarations(c_body)
        
        # Add variable declarations at the beginning
        for var_name, (var_type, is_array, init) in declarations.items():
            fortran_type = self.translate_type(var_type)
            if is_array:
                # Handle array declaration
                if init:
                    # Array with initialization
                    elements = re.search(r'\{(.*?)\}', init).group(1)
                    elements = [e.strip() for e in elements.split(',')]
                    size = len(elements)
                    fortran_body += self.indent() + f"{fortran_type}, dimension({size}) :: {var_name} = [{', '.join(elements)}]\n"
                else:
                    # Array without initialization
                    fortran_body += self.indent() + f"{fortran_type}, dimension(:) :: {var_name}\n"
            else:
                # Simple variable declaration
                fortran_body += self.indent() + f"{fortran_type} :: {var_name}\n"
                
        # Add required variables for I/O
        if "scanf" in c_body:
            fortran_body += self.indent() + "integer :: result  ! For I/O status\n"
            
        fortran_body += "\n"
        
        # Get all lines
        c_lines = c_body.split('\n')
        
        # Process line by line with handling of blocks
        i = 0
        block_stack = []  # To track nested blocks
        
        while i < len(c_lines):
            line = c_lines[i].strip()
            
            # Skip empty lines
            if not line:
                i += 1
                continue
                
            # Skip variable declarations (already handled)
            if self.is_declaration(line):
                i += 1
                continue
            
            # Handle return statements
            if line.startswith('return'):
                return_val = line.replace('return', '').replace(';', '').strip()
                if return_val:
                    if is_main:
                        fortran_body += self.indent() + f"! Return {return_val} (ignored in main)\n"
                    else:
                        fortran_body += self.indent() + f"{self.current_function}_result = {self.translate_expression(return_val)}\n"
                i += 1
                continue
            
            # Handle if statements
            if line.startswith('if') and '(' in line and ')' in line:
                # Extract condition
                condition = line[line.find('(')+1:line.rfind(')')].strip()
                fortran_body += self.translate_if_start(condition)
                
                # Check for single-line if without braces
                if ';' in line and not '{' in line:
                    # Single line if - handle the statement
                    statement = line[line.rfind(')')+1:].strip().rstrip(';')
                    self.indent_level += 1
                    
                    # Translate the single statement
                    if statement.startswith('return'):
                        return_val = statement.replace('return', '').strip()
                        if return_val:
                            if is_main:
                                fortran_body += self.indent() + f"! Return {return_val} (ignored in main)\n"
                            else:
                                fortran_body += self.indent() + f"{self.current_function}_result = {self.translate_expression(return_val)}\n"
                    elif statement.startswith('printf'):
                        fortran_body += self.translate_printf(statement)
                    else:
                        fortran_body += self.indent() + self.translate_expression(statement) + "\n"
                    
                    self.indent_level -= 1
                    fortran_body += self.translate_if_end()
                    i += 1
                    continue
                
                # Block if - find matching brace
                block_stack.append(('if', self.indent_level))
                self.indent_level += 1
                i += 1
                continue
            
            # Handle else if
            if line.startswith('else if') and '(' in line and ')' in line:
                condition = line[line.find('(')+1:line.rfind(')')].strip()
                fortran_body += self.translate_else_if(condition)
                
                # Check for single-line else if without braces
                if ';' in line and not '{' in line:
                    # Single line else if - handle the statement
                    statement = line[line.rfind(')')+1:].strip().rstrip(';')
                    self.indent_level += 1
                    
                    # Translate the single statement
                    if statement.startswith('return'):
                        return_val = statement.replace('return', '').strip()
                        if return_val:
                            if is_main:
                                fortran_body += self.indent() + f"! Return {return_val} (ignored in main)\n"
                            else:
                                fortran_body += self.indent() + f"{self.current_function}_result = {self.translate_expression(return_val)}\n"
                    elif statement.startswith('printf'):
                        fortran_body += self.translate_printf(statement)
                    else:
                        fortran_body += self.indent() + self.translate_expression(statement) + "\n"
                    
                    self.indent_level -= 1
                    i += 1
                    continue
                
                # Block else if - continue to next line
                self.indent_level += 1
                i += 1
                continue
            
            # Handle else
            if line.startswith('else') and not 'if' in line:
                fortran_body += self.translate_else()
                
                # Check for single-line else without braces
                if ';' in line and not '{' in line:
                    # Single line else - handle the statement
                    statement = line[line.replace('else', '', 1).strip()].strip().rstrip(';')
                    self.indent_level += 1
                    
                    # Translate the single statement
                    if statement.startswith('return'):
                        return_val = statement.replace('return', '').strip()
                        if return_val:
                            if is_main:
                                fortran_body += self.indent() + f"! Return {return_val} (ignored in main)\n"
                            else:
                                fortran_body += self.indent() + f"{self.current_function}_result = {self.translate_expression(return_val)}\n"
                    elif statement.startswith('printf'):
                        fortran_body += self.translate_printf(statement)
                    else:
                        fortran_body += self.indent() + self.translate_expression(statement) + "\n"
                    
                    self.indent_level -= 1
                    i += 1
                    continue
                
                # Block else - continue to next line
                self.indent_level += 1
                i += 1
                continue
            
            # Handle for loops
            if line.startswith('for') and '(' in line and ')' in line:
                # Extract for loop parts
                loop_parts = line[line.find('(')+1:line.rfind(')')].split(';')
                if len(loop_parts) == 3:
                    init = loop_parts[0].strip()
                    condition = loop_parts[1].strip()
                    increment = loop_parts[2].strip()
                    
                    fortran_body += self.translate_for_loop_start(init, condition, increment)
                    
                    # Check for single-line for loop without braces
                    if ';' in line[line.rfind(')')+1:] and not '{' in line:
                        # Single line for loop - handle the statement
                        statement = line[line.rfind(')')+1:].strip().rstrip(';')
                        self.indent_level += 1
                        
                        # Translate the single statement
                        if statement.startswith('return'):
                            return_val = statement.replace('return', '').strip()
                            if return_val:
                                if is_main:
                                    fortran_body += self.indent() + f"! Return {return_val} (ignored in main)\n"
                                else:
                                    fortran_body += self.indent() + f"{self.current_function}_result = {self.translate_expression(return_val)}\n"
                        elif statement.startswith('printf'):
                            fortran_body += self.translate_printf(statement)
                        else:
                            fortran_body += self.indent() + self.translate_expression(statement) + "\n"
                        
                        self.indent_level -= 1
                        fortran_body += self.translate_for_loop_end()
                        i += 1
                        continue
                    
                    # Block for loop - find matching brace
                    block_stack.append(('for', self.indent_level))
                    self.indent_level += 1
                    i += 1
                    continue
                else:
                    # Malformed for loop
                    fortran_body += self.indent() + f"! Malformed for loop: {line}\n"
                    i += 1
                    continue
            
            # Handle while loops
            if line.startswith('while') and '(' in line and ')' in line:
                # Extract condition
                condition = line[line.find('(')+1:line.rfind(')')].strip()
                fortran_body += self.translate_while_loop_start(condition)
                
                # Check for single-line while loop without braces
                if ';' in line[line.rfind(')')+1:] and not '{' in line:
                    # Single line while loop - handle the statement
                    statement = line[line.rfind(')')+1:].strip().rstrip(';')
                    self.indent_level += 1
                    
                    # Translate the single statement
                    if statement.startswith('return'):
                        return_val = statement.replace('return', '').strip()
                        if return_val:
                            if is_main:
                                fortran_body += self.indent() + f"! Return {return_val} (ignored in main)\n"
                            else:
                                fortran_body += self.indent() + f"{self.current_function}_result = {self.translate_expression(return_val)}\n"
                    elif statement.startswith('printf'):
                        fortran_body += self.translate_printf(statement)
                    else:
                        fortran_body += self.indent() + self.translate_expression(statement) + "\n"
                    
                    self.indent_level -= 1
                    fortran_body += self.translate_while_loop_end()
                    i += 1
                    continue
                
                # Block while loop - find matching brace
                block_stack.append(('while', self.indent_level))
                self.indent_level += 1
                i += 1
                continue
            
            # Handle opening braces - start of a new block
            if line == '{':
                i += 1
                continue
                
            # Handle closing braces - end of a block
            if line == '}':
                if block_stack:
                    block_type, old_indent = block_stack.pop()
                    self.indent_level = old_indent
                    
                    if block_type == 'if':
                        fortran_body += self.translate_if_end()
                    elif block_type == 'for':
                        fortran_body += self.translate_for_loop_end()
                    elif block_type == 'while':
                        fortran_body += self.translate_while_loop_end()
                else:
                    # Unmatched closing brace
                    fortran_body += self.indent() + "! Warning: unmatched closing brace\n"
                
                i += 1
                continue
            
            # Handle printf
            if line.startswith('printf'):
                fortran_body += self.translate_printf(line)
                i += 1
                continue
                
            # Handle scanf
            if line.startswith('scanf'):
                fortran_body += self.translate_scanf(line)
                i += 1
                continue
            
            # Handle general statements
            if line.endswith(';'):
                # This is a generic statement
                line = line.rstrip(';')
                
                # Check for assignment
                if '=' in line and not '==' in line and not '<=' in line and not '>=' in line and not '!=' in line:
                    parts = line.split('=', 1)
                    lhs = parts[0].strip()
                    rhs = parts[1].strip()
                    
                    # Translate both sides
                    lhs_translated = self.translate_expression(lhs)
                    rhs_translated = self.translate_expression(rhs)
                    
                    fortran_body += self.indent() + f"{lhs_translated} = {rhs_translated}\n"
                else:
                    # Other kind of statement
                    fortran_body += self.indent() + self.translate_expression(line) + "\n"
                
                i += 1
                continue
                
            # Handle comments
            if line.startswith('//'):
                comment = line[2:].strip()
                fortran_body += self.indent() + f"! {comment}\n"
                i += 1
                continue
                
            # If we reach here, we couldn't translate the line
            fortran_body += self.indent() + f"! Untranslated: {line}\n"
            i += 1
        
        return fortran_body
