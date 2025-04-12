#include <stdio.h>

int max(int a, int b) {
	if (a > b)
		return a;
	else
		return b;
}

int main() {
	int x = 7, y = 3;
	printf("Max = %d\n", max(x, y));
	return 0;
}
