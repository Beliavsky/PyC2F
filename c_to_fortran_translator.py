from util import (remove_newlines_in_quotes, get_before_inc_dec,
    remove_blank_lines)

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

    def translate_file(self, input_file, output_file,
        blank_lines_allowed = True):
        """Translate a C file to Fortran."""
        
        try:
            with open(input_file, 'r') as f:
                c_code = f.read()        
            fortran_code = self.translate_code(c_code)
            with open(output_file, 'w') as f:
                for line in fortran_code.splitlines():
                    if blank_lines_allowed or line.strip() != "":
                        f.write(line + '\n')
                
            print(f"Translation complete. Output written to {output_file}")
            return True
        except Exception as e:
            print(f"Error during translation: {str(e)}")
            raise

    def translate_code(self, c_code):
        """Translate C code to Fortran with non-main functions in a module."""
        c_code = self.remove_preprocessor_directives(c_code)
        c_functions = self.extract_functions(c_code)
        
        main_body = None
        non_main_funcs = {}
        for func_name, body in c_functions.items():
            if func_name == "main":
                main_body = body
            else:
                non_main_funcs[func_name] = body
        
        module_code = ""
        used_function_names = []
        if non_main_funcs:
            module_code += "module m_mod\n"
            module_code += "implicit none\n"
            module_code += "contains\n\n"
            for func_name, func_body in non_main_funcs.items():
                self.current_function = func_name
                func_info = self.functions[func_name]
                return_type = func_info["return_type"]
                params = func_info["params"]
                fortran_type = self.translate_type(return_type)
                if fortran_type.lower() == "void":
                    module_code += f"subroutine {func_name}("
                else:
                    module_code += f"function {func_name}("
                param_list = []
                for param in params:
                    param_name = param.split()[-1].replace("*", "").replace("&", "")
                    param_list.append(param_name)
                module_code += ", ".join(param_list)
                if fortran_type.lower() == "void":
                    module_code += ")\n"
                else:
                    module_code += f") result({func_name}_result)\n"
                module_code += "implicit none\n"
                for param in params:
                    param_parts = param.split()
                    param_type = " ".join(param_parts[:-1])
                    param_name = param_parts[-1].replace("*", "").replace("&", "")
                    fortran_type_param = self.translate_type(param_type)
                    module_code += f"  {fortran_type_param}, intent(in) :: {param_name}\n"
                if fortran_type.lower() != "void":
                    module_code += f"  {fortran_type} :: {func_name}_result\n"
                translated_body = self.translate_function_body_iterative(func_body)
                module_code += translated_body
                if fortran_type.lower() == "void":
                    module_code += f"end subroutine {func_name}\n\n"
                else:
                    module_code += f"end function {func_name}\n\n"
                used_function_names.append(func_name)
            module_code += "end module m_mod\n\n"
        
        main_prog = ""
        main_prog += "program main\n"
        if used_function_names:
            main_prog += "use m_mod, only: " + ", ".join(used_function_names) + "\n"
        main_prog += "implicit none\n\n"
        if main_body:
            self.current_function = "main"
            translated_main = self.translate_function_body_iterative(main_body, is_main=True)
            main_prog += translated_main
        else:
            main_prog += "  ! No main function found\n"
        main_prog += "\nend program main\n\n"
        
        fortran_code = module_code + main_prog
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
            return "character(len=100)"  # Arbitrary length
        elif 'char' in c_type:
            return "character"
        elif 'bool' in c_type:
            return "logical"
        elif 'void' in c_type:
            return "void"
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
                if stripped.startswith('#include'):
                    filtered_lines.append(f"! {stripped}")
        return '\n'.join(filtered_lines)

    def extract_functions(self, c_code):
        """Extract function definitions from C code."""
        func_pattern = r'(\w+)\s+(\w+)\s*\((.*?)\)\s*\{((?:[^{}]|(?:\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\}))*\}))*\}))*)\}'
        functions = {}
        for match in re.finditer(func_pattern, c_code, re.DOTALL):
            return_type = match.group(1)
            func_name = match.group(2)
            params_str = match.group(3).strip()
            body = match.group(4)
            params = []
            if params_str and params_str.lower() != "void":
                for param in params_str.split(','):
                    param = param.strip()
                    if param:
                        params.append(param)
            self.functions[func_name] = {"return_type": return_type, "params": params}
            functions[func_name] = body
        return functions

    def collect_declarations(self, c_body):
        """
        Collect variable declarations from C code.
        Return a dictionary mapping variable names to a tuple: (type, is_array, initialization).
        Handles multiple declarations in one statement.
        """
        declarations = {}
        c_lines = c_body.split('\n')
        for line in c_lines:
            line = line.strip()
            if self.is_declaration(line):
                line = line.rstrip(';')
                tokens = line.split()
                if not tokens:
                    continue
                c_type = tokens[0]
                rest = line[len(c_type):].strip()
                var_decls = rest.split(',')
                for var_decl in var_decls:
                    var_decl = var_decl.strip()
                    if '=' in var_decl:
                        var_name, init_value = var_decl.split('=', 1)
                        var_name = var_name.strip()
                        init_value = init_value.strip()
                    else:
                        var_name = var_decl
                        init_value = None
                    if '[' in var_name:
                        var_name = var_name.split('[')[0].strip()
                        declarations[var_name] = (c_type, True, init_value)
                        self.variable_types[var_name] = (c_type, True)
                    else:
                        declarations[var_name] = (c_type, False, init_value)
                        self.variable_types[var_name] = (c_type, False)
        return declarations

    def collect_for_loop_declarations(self, c_body):
        """
        Scan the function body for for-loop headers that declare variables.
        Returns a dictionary mapping variable names to Fortran declaration strings.
        """
        loop_decls = {}
        pattern = r'for\s*\(\s*(int|float|double|char|long)\s+(\w+)\s*='
        matches = re.findall(pattern, c_body)
        for c_type, var_name in matches:
            fortran_type = self.translate_type(c_type)
            loop_decls[var_name] = f"{fortran_type} :: {var_name}"
        return loop_decls

    def is_declaration(self, line):
        """Check if a line is a variable declaration."""
        line = line.strip()
        if not line or not line.endswith(';'):
            return False
        return (line.startswith('int ') or 
                line.startswith('float ') or 
                line.startswith('double ') or 
                line.startswith('char ') or
                line.startswith('long '))

    def translate_for_loop_start(self, init, condition, increment):
        """Translate the start of a C for loop to Fortran."""
        if ' ' in init and '=' in init:
            parts = init.split('=', 1)
            decl_parts = parts[0].strip().split()
            if len(decl_parts) >= 2:
                var_name = decl_parts[1].strip()
                start_val = parts[1].strip()
                init = f"{var_name}={start_val}"
        init_parts = init.split('=')
        if len(init_parts) == 2:
            loop_var = init_parts[0].strip()
            start_val = init_parts[1].strip()
        else:
            return self.indent() + f"! Failed to parse for loop: for ({init}; {condition}; {increment})\n"
        cond_parts = re.split(r'<=|<|>=|>|!=|==', condition)
        if len(cond_parts) == 2:
            end_var = cond_parts[1].strip()
            if ('<' in condition) and not ('<=' in condition):
                end_var = f"{end_var} - 1"
            elif ('>' in condition) and not ('>=' in condition):
                end_var = f"{end_var} + 1"
        else:
            return self.indent() + f"! Failed to parse for loop condition: {condition}\n"
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
        fortran_loop = self.indent() + f"do {loop_var} = {start_val}, {end_var}"
        if step != "1":
            fortran_loop += f", {step}"
        fortran_loop += "\n"
        return fortran_loop

    def translate_for_loop_end(self):
        """Translate the end of a C for loop to Fortran."""
        return self.indent() + "end do\n"

    def translate_while_loop_start(self, condition):
        """Translate the start of a C while loop to Fortran."""
        fortran_condition = self.translate_expression(condition)
        return self.indent() + "do while (" + fortran_condition + ")\n"

    def translate_while_loop_end(self):
        """Translate the end of a C while loop to Fortran."""
        return self.indent() + "end do\n"

    def translate_if_start(self, condition):
        """Translate the start of a C if statement to Fortran."""
        fortran_condition = self.translate_expression(condition)
        return self.indent() + "if (" + fortran_condition + ") then\n"

    def translate_if_end(self):
        """Translate the end of a C if statement to Fortran."""
        return self.indent() + "end if\n"

    def translate_else_if(self, condition):
        """Translate a C else if statement to Fortran."""
        fortran_condition = self.translate_expression(condition)
        return self.indent() + "else if (" + fortran_condition + ") then\n"

    def translate_else(self):
        """Translate a C else statement to Fortran."""
        return self.indent() + "else\n"

    def translate_declaration(self, c_declaration):
        """Translate a C variable declaration to Fortran."""
        c_declaration = c_declaration.rstrip(';')
        if '=' in c_declaration:
            parts = c_declaration.split('=', 1)
            declaration = parts[0].strip()
            value = parts[1].strip()
        else:
            declaration = c_declaration
            value = None
        parts = declaration.split()
        if len(parts) < 2:
            return self.indent() + f"! Failed to parse declaration: {c_declaration}\n"
        c_type = parts[0]
        var_name = parts[1]
        if '[' in var_name or (value and '{' in value):
            var_name = var_name.split('[')[0].strip()
            self.variables.add(var_name)
            fortran_type = self.translate_type(c_type)
            if value and '{' in value:
                elements = re.search(r'\{(.*?)\}', value).group(1)
                elements = [e.strip() for e in elements.split(',')]
                decl_line = f"{fortran_type}, dimension({len(elements)}) :: {var_name}"
                assign_line = f"{var_name} = [{', '.join(elements)}]"
            else:
                decl_line = f"{fortran_type}, dimension(:) :: {var_name}"
                assign_line = ""
        else:
            self.variables.add(var_name)
            fortran_type = self.translate_type(c_type)
            decl_line = f"{fortran_type} :: {var_name}"
            if value:
                assign_line = f"{var_name} = {self.translate_expression(value)}"
            else:
                assign_line = ""
        result = self.indent() + decl_line + "\n"
        if assign_line:
            result += self.indent() + assign_line + "\n"
        return result

    def translate_printf(self, c_printf):
        """Translate a C printf statement to Fortran using list-directed formatting."""
        c_printf = c_printf.rstrip(';')
        printf_match = re.match(r'printf\s*\(\s*"(.*?)"\s*(,\s*(.*))?\s*\)', c_printf)
        if not printf_match:
            return self.indent() + f"! Failed to parse printf: {c_printf}\n"
        args = printf_match.group(3) if printf_match.group(3) else ""
        fortran_print = self.indent() + "print*,"
        if args:
            arg_list = args.split(',')
            translated_args = [self.translate_expression(arg.strip()) for arg in arg_list]
            fortran_print += " " + ", ".join(translated_args)
        else:
            literal = printf_match.group(1)
            if literal:
                fortran_print += " " + f'"{literal}"'
            else:
                fortran_print += " "
        return fortran_print + "\n"

    def translate_scanf(self, c_scanf):
        """Translate a C scanf statement to Fortran read statement."""
        c_scanf = c_scanf.rstrip(';')
        scanf_match = re.match(r'scanf\s*\(\s*"([^"]*)"\s*(,\s*(.*))?\s*\)', c_scanf)
        if not scanf_match:
            return self.indent() + f"! Failed to parse scanf: {c_scanf}\n"
        format_str = scanf_match.group(1)
        args = scanf_match.group(3) if scanf_match.group(3) else ""
        var_list = []
        if args:
            for arg in args.split(','):
                arg = arg.strip()
                if arg.startswith('&'):
                    var_list.append(arg[1:])
                else:
                    var_list.append(arg)
        fortran_read = self.indent() + "read(*, *"
        fortran_read += ", iostat=result) "
        fortran_read += ", ".join(var_list)
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
        """Translate a C expression to Fortran using string replacements."""
        if not c_expr:
            return c_expr
        fortran_expr = c_expr
        fortran_expr = fortran_expr.replace('INT_MAX', 'huge(0)')
        fortran_expr = fortran_expr.replace('INT_MIN', '-huge(0)')
        fortran_expr = fortran_expr.replace('LONG_MAX', 'huge(0)')
        fortran_expr = fortran_expr.replace('NULL', 'null()')
        if '[' in fortran_expr and ']' in fortran_expr:
            array_pattern = r'(\w+)\s*\[([^]]+)\]'
            while re.search(array_pattern, fortran_expr):
                fortran_expr = re.sub(array_pattern, r'\1(\2+1)', fortran_expr)
        if '{' in fortran_expr and '}' in fortran_expr:
            array_init_pattern = r'\{([^{}]*)\}'
            fortran_expr = re.sub(array_init_pattern, r'[\1]', fortran_expr)
        fortran_expr = fortran_expr.replace('==', ' == ')
        fortran_expr = fortran_expr.replace('!=', ' /= ')
        fortran_expr = fortran_expr.replace('>=', ' >= ')
        fortran_expr = fortran_expr.replace('<=', ' <= ')
        fortran_expr = fortran_expr.replace('>', ' > ')
        fortran_expr = fortran_expr.replace('<', ' < ')
        fortran_expr = fortran_expr.replace('&&', ' .and. ')
        fortran_expr = fortran_expr.replace('||', ' .or. ')
        if fortran_expr.strip().startswith('!'):
            fortran_expr = '.not.' + fortran_expr.strip()[1:]
        sizeof_pattern = r'sizeof\s*\(\s*(\w+)\s*\)'
        if re.search(sizeof_pattern, fortran_expr):
            fortran_expr = re.sub(sizeof_pattern, r'kind(0)', fortran_expr)
        return fortran_expr

    def translate_updating_operator(self, c_line):
        """
        Translate a C updating operator (e.g. a *= b) into a Fortran assignment:
        a += b  ->  a = a + b,
        a -= b  ->  a = a - b,
        a *= b  ->  a = a * b,
        a /= b  ->  a = a / b
        """
        match = re.match(r'(\w+)\s*([\+\-\*/])=\s*(.+)', c_line)
        if match:
            var = match.group(1)
            op = match.group(2)
            expr = match.group(3).strip()
            return f"{var} = {var} {op} {expr}"
        return None

    def translate_function_body_iterative(self, c_body, is_main=False):
        """
        Translate C function body to Fortran using an iterative approach.
        All variable declarations (including those from for-loop headers) are output
        before any executable statements. For non-array variables with an initialization,
        a separate assignment is generated. Updating operators (like a += b) are translated.
        In non-main functions, return statements are converted into an assignment to the result variable.
        At the end of processing the function body, any remaining open block is flushed.
        """
        fortran_body = ""
        body_decls = self.collect_declarations(c_body)
        loop_decls = self.collect_for_loop_declarations(c_body)
        all_decls = {}
        for var_name, decl in loop_decls.items():
            all_decls[var_name] = (decl, "")
        for var_name, (var_type, is_array, init) in body_decls.items():
            fortran_type = self.translate_type(var_type)
            if is_array:
                if init:
                    elements = re.search(r'\{(.*?)\}', init).group(1)
                    elements = [e.strip() for e in elements.split(',')]
                    decl_line = f"{fortran_type}, dimension({len(elements)}) :: {var_name}"
                    assign_line = f"{var_name} = [{', '.join(elements)}]"
                else:
                    decl_line = f"{fortran_type}, dimension(:) :: {var_name}"
                    assign_line = ""
            else:
                decl_line = f"{fortran_type} :: {var_name}"
                if init is not None:
                    assign_line = f"{var_name} = {self.translate_expression(init)}"
                else:
                    assign_line = ""
            all_decls[var_name] = (decl_line, assign_line)
        # Output declarations.
        for decl_line, _ in all_decls.values():
            fortran_body += self.indent() + decl_line + "\n"
        # Then output assignments.
        for _, assign_line in all_decls.values():
            if assign_line:
                fortran_body += self.indent() + assign_line + "\n"
        if "scanf" in c_body:
            fortran_body += self.indent() + "integer :: result  ! For I/O status\n"
        fortran_body += "\n"
        c_lines = c_body.split('\n')
        i = 0
        block_stack = []
        while i < len(c_lines):
            line = c_lines[i].strip()
            if not line:
                i += 1
                continue
            if self.is_declaration(line):
                i += 1
                continue
            # Remove inline comments before processing.
            line_no_comment = line.split('//')[0].strip()
            if line_no_comment.endswith(';'):
                line_code = line_no_comment.rstrip(';').strip()
                updated = self.translate_updating_operator(line_code)
                if updated is not None:
                    fortran_body += self.indent() + updated + "\n"
                    i += 1
                    continue
            if line.startswith('return'):
                return_val = line.replace('return', '').replace(';', '').strip()
                if not is_main and return_val:
                    fortran_body += self.indent() + f"{self.current_function}_result = {self.translate_expression(return_val)}\n"
                i += 1
                continue
            if line.startswith('if') and '(' in line and ')' in line:
                condition = line[line.find('(')+1:line.rfind(')')].strip()
                fortran_body += self.translate_if_start(condition)
                if ';' in line and not '{' in line:
                    statement = line[line.rfind(')')+1:].strip().rstrip(';')
                    self.indent_level += 1
                    if statement.startswith('return'):
                        i += 1
                        continue
                    elif statement.startswith('printf'):
                        fortran_body += self.translate_printf(statement)
                    else:
                        fortran_body += self.indent() + self.translate_expression(statement) + "\n"
                    self.indent_level -= 1
                    fortran_body += self.translate_if_end()
                    i += 1
                    continue
                block_stack.append(('if', self.indent_level))
                self.indent_level += 1
                i += 1
                continue
            if line.startswith('else if') and '(' in line and ')' in line:
                condition = line[line.find('(')+1:line.rfind(')')].strip()
                fortran_body += self.translate_else_if(condition)
                if ';' in line and not '{' in line:
                    statement = line[line.rfind(')')+1:].strip().rstrip(';')
                    self.indent_level += 1
                    if statement.startswith('return'):
                        i += 1
                        continue
                    elif statement.startswith('printf'):
                        fortran_body += self.translate_printf(statement)
                    else:
                        fortran_body += self.indent() + self.translate_expression(statement) + "\n"
                    self.indent_level -= 1
                    i += 1
                    continue
                self.indent_level += 1
                i += 1
                continue
            if line.startswith('else') and not 'if' in line:
                fortran_body += self.translate_else()
                if ';' in line and not '{' in line:
                    statement = line[line.replace('else', '', 1).strip()].strip().rstrip(';')
                    self.indent_level += 1
                    if statement.startswith('return'):
                        i += 1
                        continue
                    elif statement.startswith('printf'):
                        fortran_body += self.translate_printf(statement)
                    else:
                        fortran_body += self.indent() + self.translate_expression(statement) + "\n"
                    self.indent_level -= 1
                    i += 1
                    continue
                self.indent_level += 1
                i += 1
                continue
            if line.startswith('for') and '(' in line and ')' in line:
                loop_parts = line[line.find('(')+1:line.rfind(')')].split(';')
                if len(loop_parts) == 3:
                    init = loop_parts[0].strip()
                    condition = loop_parts[1].strip()
                    increment = loop_parts[2].strip()
                    fortran_body += self.translate_for_loop_start(init, condition, increment)
                    if ';' in line[line.rfind(')')+1:] and not '{' in line:
                        statement = line[line.rfind(')')+1:].strip().rstrip(';')
                        self.indent_level += 1
                        if statement.startswith('return'):
                            i += 1
                            continue
                        elif statement.startswith('printf'):
                            fortran_body += self.translate_printf(statement)
                        else:
                            fortran_body += self.indent() + self.translate_expression(statement) + "\n"
                        self.indent_level -= 1
                        fortran_body += self.translate_for_loop_end()
                        i += 1
                        continue
                    block_stack.append(('for', self.indent_level))
                    self.indent_level += 1
                    i += 1
                    continue
            if line.startswith('while') and '(' in line and ')' in line:
                condition = line[line.find('(')+1:line.rfind(')')].strip()
                fortran_body += self.translate_while_loop_start(condition)
                if ';' in line[line.rfind(')')+1:] and not '{' in line:
                    statement = line[line.rfind(')')+1:].strip().rstrip(';')
                    self.indent_level += 1
                    if statement.startswith('return'):
                        i += 1
                        continue
                    elif statement.startswith('printf'):
                        fortran_body += self.translate_printf(statement)
                    else:
                        fortran_body += self.indent() + self.translate_expression(statement) + "\n"
                    self.indent_level -= 1
                    fortran_body += self.translate_while_loop_end()
                    i += 1
                    continue
                block_stack.append(('while', self.indent_level))
                self.indent_level += 1
                i += 1
                continue
            if line == '{':
                i += 1
                continue
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
                    fortran_body += self.indent() + "! Warning: unmatched closing brace\n"
                i += 1
                continue
            if line.startswith('printf'):
                fortran_body += self.translate_printf(line)
                i += 1
                continue
            if line.startswith('scanf'):
                fortran_body += self.translate_scanf(line)
                i += 1
                continue
            if line.endswith(';'):
                line = line.rstrip(';')
                if '=' in line and not '==' in line and not '<=' in line and not '>=' in line and not '!=' in line:
                    parts = line.split('=', 1)
                    lhs = parts[0].strip()
                    rhs = parts[1].strip()
                    lhs_translated = self.translate_expression(lhs)
                    rhs_translated = self.translate_expression(rhs)
                    fortran_body += self.indent() + f"{lhs_translated} = {rhs_translated}\n"
                else:
                    fortran_body += self.indent() + self.translate_expression(line) + "\n"
                i += 1
                continue
            if line.startswith('//'):
                comment = line[2:].strip()
                fortran_body += self.indent() + f"! {comment}\n"
                i += 1
                continue
            print("line:", line) # debug
            var_name, xop = get_before_inc_dec(line)
            if xop == "++" or xop == "--":
                fortran_line = var_name + " = " + var_name + " " + xop[0] + " 1"
                fortran_body += self.indent() + fortran_line + "\n"
            i += 1
        # Flush any remaining open blocks.
        while block_stack:
            block_type, old_indent = block_stack.pop()
            self.indent_level = old_indent
            if block_type == 'if':
                fortran_body += self.indent() + "end if\n"
            elif block_type == 'for':
                fortran_body += self.indent() + "end do\n"
            elif block_type == 'while':
                fortran_body += self.indent() + "end do\n"
        fortran_body = remove_newlines_in_quotes(fortran_body)
        return fortran_body
