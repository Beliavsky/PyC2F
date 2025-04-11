@echo off
:: wrapper for Python program that compiles and runs
:: the C and Fortran codes
python main.py %1.c %1.f90
if exist a.exe del a.exe
gcc %1.c
echo.
echo C output
if exist a.exe a.exe
if exist a.exe del a.exe
gfortran %1.f90
echo.
echo Fortran output
if exist a.exe a.exe
