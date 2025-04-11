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
