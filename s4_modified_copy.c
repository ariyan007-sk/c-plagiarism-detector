#include <stdio.h>

/* Type 3 copy: same program, but statements changed and re-ordered */
int main(void) {
    int marks[5];
    int i = 0, j, n = 5, temp;
    int sum = 0;
    float avg;

    printf("Enter %d marks:\n", n);
    while (i < n) {
        scanf("%d", &marks[i]);
        i++;
    }
    for (i = 0; i < n; i++)
        sum += marks[i];

    for (i = 0; i < n - 1; i++) {
        for (j = 0; j < n - i - 1; j++) {
            if (marks[j + 1] < marks[j]) {
                temp = marks[j + 1];
                marks[j + 1] = marks[j];
                marks[j] = temp;
            }
        }
    }
    avg = sum / n;               // average moved after sorting

    printf("Sorted marks: ");
    i = 0;
    while (i < n) {
        printf("%d ", marks[i]);
        i++;
    }
    printf("\nAverage = %.2f\n", avg);
    for (i = 0; i < n; i++)
        printf("*");
    printf("\n");
    return 0;
}
