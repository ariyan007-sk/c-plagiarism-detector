#include <stdio.h>

// Student solution: arrange scores in order
int main(void) {
    int score[5];
    int a, b, size = 5, hold;
    int total = 0;
    float mean;

    printf("Please type %d scores:\n", size);
    for (a = 0; a < size; a++) {
        scanf("%d", &score[a]);
        total = total + score[a];
    }
    mean = total / size;

    for (a = 0; a < size - 1; a++) {
        for (b = 0; b < size - a - 1; b++) {
            if (score[b] > score[b + 1]) {
                hold = score[b];
                score[b] = score[b + 1];
                score[b + 1] = hold;
            }
        }
    }

    printf("Result in order: ");
    for (a = 0; a < size; a++)
        printf("%d ", score[a]);
    printf("\nMean value = %.2f\n", mean);
    return 0;
}
