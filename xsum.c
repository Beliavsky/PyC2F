#include <stdio.h>

int main() {
	int sum = 0;
	int i;
	for (i = 1; i <= 5; i++) {
		sum += i;  // sum = sum + i
	}
	printf("Sum = %d\n", sum);
	return 0;
}
