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

gives a Fortran code that compiles but has an extraneous "I0":

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

Running it on the C code

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
	int test_cases[] = {0, 1, 5, 10, 12, 20, -1};
	int num_tests = sizeof(test_cases) / sizeof(test_cases[0]);

	printf("Factorial Test Program\n");
	printf("=====================\n\n");

	for (int i = 0; i < num_tests; i++) {
		int n = test_cases[i];
		printf("factorial(%d) = ", n);

		int result = factorial(n);

		if (result > 0 || n == 0) {
			printf("%d\n", result);
		}
	}

    // Interactive test
	int num;
	printf("\nEnter a number to compute its factorial (or -1 to quit): ");
	while (scanf("%d", &num) == 1 && num != -1) {
		printf("factorial(%d) = ", num);

		unsigned long long result = factorial(num);

		if (result > 0 || num == 0) {
			printf("%llu\n", result);
		}

		printf("Enter a number to compute its factorial (or -1 to quit): ");
	}

	return 0;
}
```

gives invalid Fortran code:

```fortran
! Translated from C to Fortran
program main
  implicit none

integer, dimension(7) :: test_cases = [0, 1, 5, 10, 12, 20, -1]
integer, dimension(:) :: num_tests
integer, dimension(:) :: n
integer :: result
integer :: num
integer :: result  ! For I/O status

print *, "Factorial Test Program"
print *, "====================="
integer :: i
do i = 0, num_tests - 1
  write(*, '(A)', advance='no') "factorial((I0)) = "
  write(*, '(A)', advance='no') n
  if (result  >  0  .or.  n  ==  0) then
    print *, "I0", result
  end if
end do
! Interactive test
print *, "Enter a number to compute its factorial (or -1 to quit): "
do while (scanf("%d", &num)  ==  1  .and.  num  /=  -1)
  write(*, '(A)', advance='no') "factorial((I0)) = "
  write(*, '(A)', advance='no') num
  unsigned long long result = factorial(num)
  if (result  >  0  .or.  num  ==  0) then
    print *, "%llu", result
  end if
  print *, "Enter a number to compute its factorial (or -1 to quit): "
end do
! Return 0 (ignored in main)

end program main

function factorial(n) result(factorial_result)
  implicit none
  integer, intent(in) :: n
  integer :: factorial_result
integer :: result

! Base case: factorial of 0 is 1
if (n  ==  0) then
  factorial_result = 1
  ! Handle negative input
  if (n  <  0) then
    print *, "Error: Factorial not defined for negative numbers"
    factorial_result = 0
  end if
  ! Compute factorial using iteration
  integer :: i
  do i = 1, n
    ! Check for overflow (simplified for int type)
    if (result  >  huge(0) / i) then
      print *, "Error: Factorial overflow"
      factorial_result = 0
    end if
    result * = i
  end do
  factorial_result = result
end function factorial
```
