# PyC2F
Partial translator from C to Fortran in Python. Works for only a few simple programs.
Running

`python main.py xij.c xij.f90` for the C code `xij.c`

```c
#include <stdio.h>

int main() {
	int i;
	int j;
	i = 2;
	j = 3;
	printf("%d %d %d\n", i, j, i + j);
	return 0;
}
```

gives a Fortran code

```Fortran
program main
implicit none
integer :: i
integer :: j

i = 2
j = 3
print*, i, j, i + j

end program main
```

Running it on the C code

```c
#include <stdio.h>

int main() {
	printf("Number Square Cube\n");
	for (int i = 1; i <= 10; i++) {
		printf("%d\t%d\t%d\n", i, i * i, i * i * i);
	}
	return 0;
}
```

gives

```fortran
program main
  implicit none

integer :: i

print*, "Number Square Cube"
do i = 1, 10
  print*, i, i * i, i * i * i
end do

end program main
```

Running on
```c
#include <stdio.h>

int main() {
	int a = 10, b = 5;
	printf("a, b = %d %d \n", a, b);
	a += b;  // a becomes 15
	printf("After a += b: a = %d\n", a);
	a -= 3;  // a becomes 12
	printf("After a -= 3: a = %d\n", a);
	a *= 2;  // a becomes 24
	printf("After a *= 2: a = %d\n", a);
	a /= 4;  // a becomes 6
	printf("After a /= 4: a = %d\n", a);

	return 0;
}
```
gives
```fortran
program main
  implicit none

integer :: a
integer :: b
a = 10
b = 5

print*, a, b
a = a + b
print*, a
a = a - 3
print*, a
a = a * 2
print*, a
a = a / 4
print*, a

end program main
```

Running on
```c
#include <stdio.h>
#include <limits.h>

// Function to compute factorial of an integer
int factorial(int n) {
    // Base case: factorial of 0 is 1
	if (n == 0)
		return 1;
    // Handle negative input
	if (n < 0) {
		printf("Error: Factorial not defined for negative numbers\n");
		return 0;
	}
	int result = 1;
    // Compute factorial using iteration
	for (int i = 1; i <= n; i++) {
	// Check for overflow (simplified for int type)
		if (result > INT_MAX / i) {
			printf("Error: Factorial overflow\n");
			return 0;
		}
		result *= i;
	}
	return result;
}

int main() {
	printf("factorial(3) = %d", factorial(3));
	return 0;
}
```

gives an incorrect Fortran code where the case n /= 0 is not handled in the function
```fortran
module m_mod
  implicit none
contains

function factorial(n) result(factorial_result)
  implicit none
  integer, intent(in) :: n
  integer :: factorial_result
integer :: i
integer :: result
result = 1

! Base case: factorial of 0 is 1
if (n  ==  0) then
  factorial_result = 1
  ! Handle negative input
  if (n  <  0) then
    print*, "Error: Factorial not defined for negative numbers"
    factorial_result = 0
  end if
  ! Compute factorial using iteration
  do i = 1, n
    ! Check for overflow (simplified for int type)
    if (result  >  huge(0) / i) then
      print*, "Error: Factorial overflow"
      factorial_result = 0
    end if
    result = result * i
  end do
  factorial_result = result
end if
end function factorial

end module m_mod

program main
use m_mod, only: factorial
  implicit none


print*, factorial(3)

end program main
```
