package com.kenhlive.tv

import com.kenhlive.tv.model.MatchState
import com.kenhlive.tv.model.SportSource
import com.kenhlive.tv.repository.SportsRepository
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class SportsJsonParsingTest {

    @Test
    fun socoliveBackboneEnrichedWithLiveScoreWithoutFakeUpcomingScore() {
        val now = 1_700_000_000_000L
        val socoliveJson = """
            {
              "data": [
                {
                  "id": "live1",
                  "hostName": "Bayern München",
                  "guestName": "Borussia Dortmund",
                  "matchTime": ${now - 30 * 60_000L},
                  "isLive": true,
                  "m3u8": "https://example.com/live1.m3u8"
                },
                {
                  "id": "up1",
                  "hostName": "Arsenal",
                  "guestName": "Chelsea",
                  "matchTime": ${now + 4 * 3600_000L},
                  "title": "02:00 Arsenal vs Chelsea"
                }
              ]
            }
        """.trimIndent()

        val colaJson = """
            [
              {
                "homeName": "FC Bayern Munchen",
                "awayName": "Dortmund",
                "timestamp": ${now - 30 * 60_000L},
                "isLive": true,
                "homeScore": 2,
                "awayScore": 1,
                "m3u8": "https://cola.example.com/1.m3u8"
              }
            ]
        """.trimIndent()

        val repo = SportsRepository()
        val backbone = repo.parseSocolive(socoliveJson, null, now).toMutableList()
        val enrich = repo.parseGenericEnrichment(colaJson, SportSource.COLATV, now)
        val merged = repo.mergeEnrichments(backbone, enrich)

        assertEquals(2, merged.size)
        val live = merged.first { it.id == "live1" }
        assertEquals(MatchState.LIVE, live.state)
        assertEquals(2, live.hostScore)
        assertEquals(1, live.guestScore)
        assertEquals(2, live.streams.size)

        val upcoming = merged.first { it.id == "up1" }
        assertEquals(MatchState.UPCOMING, upcoming.state)
        assertNull(upcoming.hostScore)
        assertNull(upcoming.guestScore)
        assertEquals("VS", upcoming.displayScoreOrVs())
    }
}
