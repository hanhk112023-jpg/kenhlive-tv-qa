package com.kenhlive.tv.logic

import com.kenhlive.tv.model.MatchState

data class ParsedScore(
    val hostScore: Int? = null,
    val guestScore: Int? = null
)

object ScoreParser {

    // Matches explicit score patterns like "2 - 1", "2:1", "108-102", "108 : 102"
    private val SCORE_REGEX = Regex("""\b(\d{1,3})\s*[-:]\s*(\d{1,3})\b""")
    // Matches HH:mm time strings like "02:00", "03:00", "04:30", "19:45"
    private val TIME_HH_MM_REGEX = Regex("""^\s*([01]\d|2[0-3]):([0-5]\d)\s*$""")

    fun parseScoreFromText(text: String?, state: MatchState): ParsedScore {
        // Rule 7.2: Upcoming matches NEVER have scores; "02:00", "03:00", "04:30" are kickoff times.
        if (state == MatchState.UPCOMING || text.isNullOrBlank()) {
            return ParsedScore(null, null)
        }

        // If the entire string is a pure HH:mm kickoff time like "02:00", reject it as a score.
        if (TIME_HH_MM_REGEX.matches(text)) {
            return ParsedScore(null, null)
        }

        val match = SCORE_REGEX.find(text) ?: return ParsedScore(null, null)
        val fullToken = match.value.trim()
        // If matched token is HH:mm with leading zero on first part and colon (no spaces), e.g., "02:00" or "04:30",
        // treat as time unless surrounded by score context; wait: "02:00" in "02:00 Arsenal vs Chelsea" is kickoff time!
        val hStr = match.groupValues[1]
        val aStr = match.groupValues[2]
        if (fullToken.contains(":") && !fullToken.contains(" ") && hStr.length == 2 && hStr.startsWith("0") && (aStr == "00" || aStr == "15" || aStr == "30" || aStr == "45")) {
            return ParsedScore(null, null)
        }

        val h = hStr.toIntOrNull()
        val g = aStr.toIntOrNull()
        if (h == null || g == null || h < 0 || g < 0) {
            return ParsedScore(null, null)
        }
        // Supports 3-digit scores (e.g. NBA 108-102) without capping at 15
        return ParsedScore(h, g)
    }

    fun parseNumericScores(hostRaw: Any?, guestRaw: Any?, state: MatchState): ParsedScore {
        if (state == MatchState.UPCOMING) {
            return ParsedScore(null, null)
        }
        val h = parseSingleInt(hostRaw)
        val g = parseSingleInt(guestRaw)
        return if (h != null && g != null && h >= 0 && g >= 0) {
            ParsedScore(h, g)
        } else {
            ParsedScore(null, null)
        }
    }

    private fun parseSingleInt(raw: Any?): Int? {
        if (raw == null) return null
        if (raw is Number) return raw.toInt()
        val s = raw.toString().trim()
        if (s.isEmpty() || s.equals("null", ignoreCase = true) || s == "-") return null
        return s.toIntOrNull()
    }

    fun resolveHeroScore(
        enrichedHost: Int?,
        enrichedGuest: Int?,
        roomTitle: String?,
        state: MatchState
    ): ParsedScore {
        if (state == MatchState.UPCOMING) return ParsedScore(null, null)
        val parsed = parseScoreFromText(roomTitle, state)
        val h = enrichedHost ?: parsed.hostScore
        val g = enrichedGuest ?: parsed.guestScore
        return if (h != null && g != null) ParsedScore(h, g) else ParsedScore(null, null)
    }
}
