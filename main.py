#!/usr/bin/env python3
"""
An improved C to Fortran translator that handles common syntax elements.
This version is fully iterative to avoid recursion depth issues.

Major improvements:
- Proper function placement in Fortran structure
- Better array handling
- Corrected loop variable declarations
- C constants replaced with Fortran equivalents
- Improved I/O handling
- Better type handling

Usage: python improved_c_to_fortran.py input.c output.f90
"""

import sys
import os.path
from c_to_fortran_translator import CToFortranTranslator

def main():
    if len(sys.argv) != 3:
        print("Usage: python improved_c_to_fortran.py input.c output.f90")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
        sys.exit(1)
    
    try:
        translator = CToFortranTranslator()
        if translator.translate_file(input_file, output_file):
            print("Successfully translated C code to Fortran.")
    except Exception as e:
        print(f"Error during translation: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
