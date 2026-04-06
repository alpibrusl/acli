package acli

// SuggestFlag returns a close known flag name or "" (spec §4.1).
func SuggestFlag(unknown string, known []string) string {
	best := ""
	bestDist := 3
	for _, k := range known {
		d := levenshtein(unknown, k)
		if d < bestDist {
			bestDist = d
			best = k
		}
	}
	return best
}

func levenshtein(a, b string) int {
	ra, rb := []rune(a), []rune(b)
	la, lb := len(ra), len(rb)
	if la == 0 {
		return lb
	}
	if lb == 0 {
		return la
	}
	m := make([][]int, la+1)
	for i := range m {
		m[i] = make([]int, lb+1)
		m[i][0] = i
	}
	for j := 0; j <= lb; j++ {
		m[0][j] = j
	}
	for i := 1; i <= la; i++ {
		for j := 1; j <= lb; j++ {
			cost := 0
			if ra[i-1] != rb[j-1] {
				cost = 1
			}
			m[i][j] = min3(m[i-1][j]+1, m[i][j-1]+1, m[i-1][j-1]+cost)
		}
	}
	return m[la][lb]
}

func min3(a, b, c int) int {
	if a <= b && a <= c {
		return a
	}
	if b <= c {
		return b
	}
	return c
}
