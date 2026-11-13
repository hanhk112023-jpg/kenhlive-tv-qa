package com.kenhlive.tv

import com.kenhlive.tv.logic.TeamNameMatcher
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class TeamNameMatcherTest {

    @Test
    fun unicodeNfdNormalizationWorks() {
        assertEquals("atletico", TeamNameMatcher.normalize("Atlético"))
        assertEquals("bayern munchen", TeamNameMatcher.normalize("Bayern München"))
        assertEquals("sao paulo", TeamNameMatcher.normalize("São Paulo"))
    }

    @Test
    fun threeTierMatchingAndKickoffWindow() {
        val baseTime = 1_700_000_000_000L
        // Tier 1: Exact after accent strip
        assertTrue(TeamNameMatcher.isSameTeam("São Paulo", "Sao Paulo"))
        // Tier 2: Simplified legal prefix/suffix
        assertTrue(TeamNameMatcher.isSameTeam("FC Bayern München", "Bayern Munchen"))
        // Tier 3: Token overlap >= 80% AND kickoff < 2h
        assertTrue(
            TeamNameMatcher.isSameTeam(
                "Club Atletico Progreso",
                "Progreso",
                baseTime,
                baseTime + 1_800_000L
            )
        )
        // Reject Tier 3 if kickoff >= 2h apart
        assertFalse(
            TeamNameMatcher.isSameTeam(
                "Club Atletico Progreso",
                "Progreso",
                baseTime,
                baseTime + 3 * 3600_000L
            )
        )
    }

    @Test
    fun ageSuffixesU20U21U23AreNeverStripped() {
        assertFalse(TeamNameMatcher.isSameTeam("Arsenal U23", "Arsenal"))
        assertFalse(TeamNameMatcher.isSameTeam("Vietnam U23", "Vietnam U21"))
        assertFalse(TeamNameMatcher.isSameTeam("Brazil U20", "Brazil"))
        assertTrue(TeamNameMatcher.isSameTeam("Arsenal U23", "Arsenal FC U23"))
    }

    @Test
    fun sameCityRivalsAreNeverMerged() {
        assertFalse(TeamNameMatcher.isSameTeam("Man City", "Man Utd"))
        assertFalse(TeamNameMatcher.isSameTeam("Real Madrid", "Atletico Madrid"))
        assertFalse(TeamNameMatcher.isSameTeam("AC Milan", "Inter Milan"))
    }
}
