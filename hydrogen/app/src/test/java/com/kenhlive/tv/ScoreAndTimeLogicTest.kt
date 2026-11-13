package com.kenhlive.tv

import com.kenhlive.tv.logic.ScoreParser
import com.kenhlive.tv.logic.TimeUtils
import com.kenhlive.tv.logic.VersionComparator
import com.kenhlive.tv.model.MatchModel
import com.kenhlive.tv.model.MatchState
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import java.util.Calendar

class ScoreAndTimeLogicTest {

    @Test
    fun upcomingEarlyMorningKickoffNeverBecomesFakeScore() {
        val earlyMorningTimes = listOf("01:00", "02:00", "03:00", "04:30", "09:00")
        for (timeStr in earlyMorningTimes) {
            val parsed = ScoreParser.parseScoreFromText(timeStr, MatchState.UPCOMING)
            assertNull("Host score must be null for $timeStr", parsed.hostScore)
            assertNull("Guest score must be null for $timeStr", parsed.guestScore)

            val match = MatchModel(
                id = "m_$timeStr",
                homeTeam = "Arsenal",
                awayTeam = "Chelsea",
                kickoffEpochMs = System.currentTimeMillis() + 3600_000L,
                state = MatchState.UPCOMING,
                hostScore = parsed.hostScore,
                guestScore = parsed.guestScore
            )
            assertEquals("VS", match.displayScoreOrVs())
        }
    }

    @Test
    fun midnightCrossingMatchDoesNotFlipState() {
        val calNow = Calendar.getInstance(TimeUtils.VN_TIMEZONE).apply {
            set(2026, Calendar.NOVEMBER, 13, 23, 55, 0)
            set(Calendar.MILLISECOND, 0)
        }
        val calKickoffNextDay = Calendar.getInstance(TimeUtils.VN_TIMEZONE).apply {
            set(2026, Calendar.NOVEMBER, 14, 0, 15, 0)
            set(Calendar.MILLISECOND, 0)
        }
        // At 23:55, a 00:15 match next day is UPCOMING, NOT LIVE
        val stateBeforeMidnight = TimeUtils.computeMatchState(
            kickoffEpochMs = calKickoffNextDay.timeInMillis,
            nowEpochMs = calNow.timeInMillis
        )
        assertEquals(MatchState.UPCOMING, stateBeforeMidnight)

        // At 00:10 next day, a 23:45 match from previous day is LIVE, NOT UPCOMING
        val calPrevKickoff = Calendar.getInstance(TimeUtils.VN_TIMEZONE).apply {
            set(2026, Calendar.NOVEMBER, 13, 23, 45, 0)
            set(Calendar.MILLISECOND, 0)
        }
        val calAfterMidnight = Calendar.getInstance(TimeUtils.VN_TIMEZONE).apply {
            set(2026, Calendar.NOVEMBER, 14, 0, 10, 0)
            set(Calendar.MILLISECOND, 0)
        }
        val stateAfterMidnight = TimeUtils.computeMatchState(
            kickoffEpochMs = calPrevKickoff.timeInMillis,
            nowEpochMs = calAfterMidnight.timeInMillis
        )
        assertEquals(MatchState.LIVE, stateAfterMidnight)
    }

    @Test
    fun supportsThreeDigitNbaScoresAndFinishedScores() {
        val nba = ScoreParser.parseScoreFromText("Lakers 108-102 Celtics", MatchState.LIVE)
        assertEquals(108, nba.hostScore)
        assertEquals(102, nba.guestScore)

        val finished = ScoreParser.parseNumericScores(3, 1, MatchState.FINISHED)
        assertEquals(3, finished.hostScore)
        assertEquals(1, finished.guestScore)
    }

    @Test
    fun heroBannerUsesEnrichedScoreFirst() {
        val hero = ScoreParser.resolveHeroScore(
            enrichedHost = 2,
            enrichedGuest = 1,
            roomTitle = "Arsenal vs Chelsea",
            state = MatchState.LIVE
        )
        assertEquals(2, hero.hostScore)
        assertEquals(1, hero.guestScore)
    }

    @Test
    fun versionComparatorIsFailClosedOnMalformedVersions() {
        assertTrue(VersionComparator.isNewerVersion("0.1.13", "0.1.12"))
        assertFalse(VersionComparator.isNewerVersion("0.1.12", "0.1.12"))
        assertFalse(VersionComparator.isNewerVersion("0.1.11", "0.1.12"))
        assertFalse(VersionComparator.isNewerVersion("invalid-ver", "0.1.12"))
        assertFalse(VersionComparator.isNewerVersion("", "0.1.12"))
        assertFalse(VersionComparator.isNewerVersion(null, "0.1.12"))
    }
}
