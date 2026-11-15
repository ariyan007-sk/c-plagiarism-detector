#include <stdio.h>

/* Print all prime numbers up to a limit */
int is_prime(int x) {
    int d;
    if (x < 2)
        return 0;
    for (d = 2; d * d <= x; d++) {
        if (x % d == 0)
            return 0;
    }
    return 1;
}

int main(void) {
    int limit, v, count = 0;

    printf("Enter the limit: ");
    scanf("%d", &limit);

    printf("Primes up to %d:\n", limit);
    for (v = 2; v <= limit; v++) {
        if (is_prime(v)) {
            printf("%d ", v);
            count++;
        }
    }
    printf("\nTotal primes = %d\n", count);
    return 0;
}
