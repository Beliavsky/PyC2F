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
