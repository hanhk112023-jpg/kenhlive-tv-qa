package com.kenhlive.tv.logic

import java.text.Normalizer
import java.util.Locale
import java.util.concurrent.ConcurrentHashMap
import kotlin.math.abs

object TeamNameMatcher {

    private const val TWO_HOURS_MS = 2L * 60L * 60L * 1000L

    private val normalizeCache = ConcurrentHashMap<String, String>()
    private val simplifiedCache = ConcurrentHashMap<String, String>()

    private val NON_ALNUM_REGEX = Regex("[^a-z0-9\\s]")
    private val MULTI_SPACE_REGEX = Regex("\\s+")
    private val COMBINING_MARKS_REGEX = Regex("\\p{InCombiningDiacriticalMarks}+")

    // Legal prefixes/suffixes & state codes to strip in Tier 2.
    // NEVER strip age suffixes like U20, U21, U23, U19, U17!
    private val MULTI_WORD_STRIP = listOf(
        "club atletico",
        "sporting club"
    )

    private val SINGLE_TOKEN_STRIP = setOf(
        "ca", "cd", "cs", "deportivo", "fc", "cf", "sc", "ac",
        "clb", "club", "afc", "pr", "sp", "rj", "mg"
    )

    // Distinct same-city or rival club tokens that must never be cross-matched
    private val CONFLICT_PAIRS = listOf(
        setOf("city") to setOf("utd", "united"),
        setOf("real") to setOf("atletico"),
        setOf("ac") to setOf("inter"),
        setOf("espanyol") to setOf("barcelona"),
        setOf("everton") to setOf("liverpool"),
        setOf("arsenal") to setOf("chelsea", "tottenham")
    )

    private val AGE_GROUP_REGEX = Regex("\\bu(1[6-9]|2[0-3])\\b")

    fun normalize(raw: String): String {
        return normalizeCache.getOrPut(raw) {
            // Handle special characters that NFD doesn't decompose into base ASCII (e.g. đ -> d, ø -> o, ł -> l)
            val preReplaced = raw
                .replace('đ', 'd').replace('Đ', 'D')
                .replace('ø', 'o').replace('Ø', 'O')
                .replace('ł', 'l').replace('Ł', 'L')

            val decomposed = Normalizer.normalize(preReplaced, Normalizer.Form.NFD)
            val withoutAccents = COMBINING_MARKS_REGEX.replace(decomposed, "")
            withoutAccents
                .lowercase(Locale.US)
                .replace(NON_ALNUM_REGEX, " ")
                .replace(MULTI_SPACE_REGEX, " ")
                .trim()
        }
    }

    fun simplify(raw: String): String {
        return simplifiedCache.getOrPut(raw) {
            var s = normalize(raw)
            for (phrase in MULTI_WORD_STRIP) {
                s = s.replace(Regex("\\b$phrase\\b"), " ")
            }
            val tokens = s.split(" ").filter { token ->
                token.isNotEmpty() && token !in SINGLE_TOKEN_STRIP
            }
            tokens.joinToString(" ").trim()
        }
    }

    fun isSameTeam(
        nameA: String,
        nameB: String,
        kickoffA: Long = 0L,
        kickoffB: Long = 0L
    ): Boolean {
        val normA = normalize(nameA)
        val normB = normalize(nameB)
        if (normA.isEmpty() || normB.isEmpty()) return false

        // Absolute rule: if either has an age suffix (U20/U21/U23), both must have the exact same age suffix
        val ageA = AGE_GROUP_REGEX.find(normA)?.value
        val ageB = AGE_GROUP_REGEX.find(normB)?.value
        if (ageA != ageB) return false

        // Anti-mismatch guard for same-city rivals
        if (hasConflictingClubTokens(normA, normB)) return false

        // Tier 1: Exact normalized match
        if (normA == normB) return true

        // Tier 2: Simplified match (legal prefixes/suffixes removed)
        val simpA = simplify(nameA)
        val simpB = simplify(nameB)
        if (simpA.isNotEmpty() && simpA == simpB) return true

        // Tier 3: Token overlap >= 80% AND kickoff within 2 hours
        if (kickoffA > 0L && kickoffB > 0L && abs(kickoffA - kickoffB) < TWO_HOURS_MS) {
            val tokensA = simpA.split(" ").filter { it.isNotEmpty() }.toSet()
            val tokensB = simpB.split(" ").filter { it.isNotEmpty() }.toSet()
            if (tokensA.isNotEmpty() && tokensB.isNotEmpty()) {
                val intersectionSize = tokensA.intersect(tokensB).size
                val minSize = minOf(tokensA.size, tokensB.size)
                val overlapRatio = intersectionSize.toDouble() / minSize.toDouble()
                if (overlapRatio >= 0.80) {
                    return true
                }
            }
        }

        return false
    }

    fun isSameMatch(
        homeA: String,
        awayA: String,
        kickoffA: Long,
        homeB: String,
        awayB: String,
        kickoffB: Long
    ): Boolean {
        return isSameTeam(homeA, homeB, kickoffA, kickoffB) &&
            isSameTeam(awayA, awayB, kickoffA, kickoffB)
    }

    private fun hasConflictingClubTokens(normA: String, normB: String): Boolean {
        val tokensA = normA.split(" ").toSet()
        val tokensB = normB.split(" ").toSet()
        for ((left, right) in CONFLICT_PAIRS) {
            val aHasLeft = tokensA.any { it in left }
            val aHasRight = tokensA.any { it in right }
            val bHasLeft = tokensB.any { it in left }
            val bHasRight = tokensB.any { it in right }
            if ((aHasLeft && bHasRight) || (aHasRight && bHasLeft)) {
                return true
            }
        }
        return false
    }

    fun clearCache() {
        normalizeCache.clear()
        simplifiedCache.clear()
    }
}
