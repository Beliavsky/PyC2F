# PyC2F
Attempt to write a partial translator from C to Fortran in Python. Currently not working. Running

`python main.py xij.c xij.f90` for the C code `xij.c`

```c
#include <stdio.h>

int main() {
	int i;
	int j;
	i = 2;
	j = 3;
	printf("%d\n", i + j);
	return 0;
}
```

gives a Fortran code with an extraneous "I0":

```fortran
! Translated from C to Fortran
program main
  implicit none

integer :: i
integer :: j

i = 2
j = 3
print *, "I0", i + j
! Return 0 (ignored in main)

end program main
```
