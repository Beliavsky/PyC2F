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
