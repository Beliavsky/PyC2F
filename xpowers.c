#include <stdio.h>

int main() {
	printf("Number Square Cube\n");
	for (int i = 1; i <= 10; i++) {
		printf("%d\t%d\t%d\n", i, i * i, i * i * i);
	}
	return 0;
}
