package dev.acli;

import java.util.List;

/** Suggest a close match for a mistyped flag per spec §4.1. */
public final class SuggestFlag {

    private SuggestFlag() {}

    public static String suggest(String unknown, List<String> known) {
        String best = null;
        int bestDist = 3;
        for (String k : known) {
            int d = levenshtein(unknown, k);
            if (d < bestDist) {
                bestDist = d;
                best = k;
            }
        }
        return best;
    }

    static int levenshtein(String a, String b) {
        int n = a.length();
        int m = b.length();
        int[][] matrix = new int[n + 1][m + 1];
        for (int i = 0; i <= n; i++) {
            matrix[i][0] = i;
        }
        for (int j = 0; j <= m; j++) {
            matrix[0][j] = j;
        }
        for (int i = 1; i <= n; i++) {
            for (int j = 1; j <= m; j++) {
                int cost = a.charAt(i - 1) == b.charAt(j - 1) ? 0 : 1;
                matrix[i][j] =
                        Math.min(
                                Math.min(matrix[i - 1][j] + 1, matrix[i][j - 1] + 1),
                                matrix[i - 1][j - 1] + cost);
            }
        }
        return matrix[n][m];
    }
}
