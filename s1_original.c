#include <stdio.h>

/* Read 5 marks, sort them (bubble sort), print them and the average */
int main(void) {
    int marks[5];
    int i, j, n = 5, temp;
    int sum = 0;
    float avg;

    printf("Enter %d marks:\n", n);
    for (i = 0; i < n; i++) {
        scanf("%d", &marks[i]);
        sum = sum + marks[i];
    }
    avg = sum / n;               // average before sorting

    for (i = 0; i < n - 1; i++) {
        for (j = 0; j < n - i - 1; j++) {
            if (marks[j] > marks[j + 1]) {
                temp = marks[j];
                marks[j] = marks[j + 1];
                marks[j + 1] = temp;
            }
        }
    }

    printf("Sorted marks: ");
    for (i = 0; i < n; i++)
        printf("%d ", marks[i]);
    printf("\nAverage = %.2f\n", avg);
    return 0;
}
