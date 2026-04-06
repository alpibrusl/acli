namespace Acli;

public static class SuggestFlag
{
    public static string? Suggest(string unknown, IEnumerable<string> known)
    {
        string? best = null;
        var bestDist = 3;
        foreach (var k in known)
        {
            var d = Levenshtein(unknown, k);
            if (d < bestDist)
            {
                bestDist = d;
                best = k;
            }
        }
        return best;
    }

    static int Levenshtein(string a, string b)
    {
        var la = a.Length;
        var lb = b.Length;
        var m = new int[la + 1, lb + 1];
        for (var i = 0; i <= la; i++) m[i, 0] = i;
        for (var j = 0; j <= lb; j++) m[0, j] = j;
        for (var i = 1; i <= la; i++)
        {
            for (var j = 1; j <= lb; j++)
            {
                var cost = a[i - 1] == b[j - 1] ? 0 : 1;
                m[i, j] = Math.Min(Math.Min(m[i - 1, j] + 1, m[i, j - 1] + 1), m[i - 1, j - 1] + cost);
            }
        }
        return m[la, lb];
    }
}
