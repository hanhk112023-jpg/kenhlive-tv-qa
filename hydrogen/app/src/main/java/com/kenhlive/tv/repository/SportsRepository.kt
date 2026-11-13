package com.kenhlive.tv.repository

import com.kenhlive.tv.logic.ScoreParser
import com.kenhlive.tv.logic.TeamNameMatcher
import com.kenhlive.tv.logic.TimeUtils
import com.kenhlive.tv.model.MatchModel
import com.kenhlive.tv.model.MatchState
import com.kenhlive.tv.model.SportSource
import com.kenhlive.tv.model.StreamSource
import com.kenhlive.tv.network.HttpClientProvider
import kotlinx.coroutines.async
import kotlinx.coroutines.coroutineScope
import org.json.JSONArray
import org.json.JSONObject

class SportsRepository {

    companion object {
        private const val SOCOLIVE_RECOMMEND = "https://json.vnres.co/match_recommend.json"
        private const val SOCOLIVE_LIVE_ROOMS = "https://json.vnres.co/all_live_rooms.json"
        private const val COLATV_API = "https://api.colaapis6.com/"
        private const val GAVANG_API = "https://gavangtv-api.adviceme.io/api/v1/matches"
        private const val GIOVANG_FIXTURES = "https://live-api.keonhacaitp.one/api/fixtures/"
        private const val GIOVANG_LIVE = "https://live-api.keonhacaitp.one/storage/livestream/live.json"
        const val ESPN_LOGO_BASE = "https://a.espncdn.com/i/teamlogos/soccer/500/"
        private const val CACHE_TTL_MS = 45_000L
    }

    @Volatile
    private var cachedMatches: List<MatchModel> = emptyList()
    @Volatile
    private var lastFetchMs: Long = 0L

    data class EnrichmentData(
        val homeTeam: String,
        val awayTeam: String,
        val kickoffEpochMs: Long,
        val homeLogo: String?,
        val awayLogo: String?,
        val hostScore: Int?,
        val guestScore: Int?,
        val minuteText: String?,
        val isLive: Boolean,
        val isFinished: Boolean,
        val stream: StreamSource?
    )

    suspend fun fetchAllMatches(
        forceRefresh: Boolean = false,
        nowEpochMs: Long = System.currentTimeMillis()
    ): List<MatchModel> {
        if (!forceRefresh && cachedMatches.isNotEmpty() && (nowEpochMs - lastFetchMs) < CACHE_TTL_MS) {
            return cachedMatches
        }

        val result = coroutineScope {
            val socoRecDeferred = async { runCatching { HttpClientProvider.getString(SOCOLIVE_RECOMMEND) }.getOrNull() }
            val socoLiveDeferred = async { runCatching { HttpClientProvider.getString(SOCOLIVE_LIVE_ROOMS) }.getOrNull() }
            val colaDeferred = async { runCatching { HttpClientProvider.getString(COLATV_API) }.getOrNull() }
            val gavangDeferred = async { runCatching { HttpClientProvider.getString(GAVANG_API) }.getOrNull() }
            val giovangFixDeferred = async { runCatching { HttpClientProvider.getString(GIOVANG_FIXTURES) }.getOrNull() }
            val giovangLiveDeferred = async { runCatching { HttpClientProvider.getString(GIOVANG_LIVE) }.getOrNull() }

            val backbone = parseSocolive(
                socoRecDeferred.await(),
                socoLiveDeferred.await(),
                nowEpochMs
            ).toMutableList()

            val enrichments = mutableListOf<EnrichmentData>()
            enrichments += parseGenericEnrichment(colaDeferred.await(), SportSource.COLATV, nowEpochMs)
            enrichments += parseGenericEnrichment(gavangDeferred.await(), SportSource.GAVANG, nowEpochMs)
            enrichments += parseGenericEnrichment(giovangFixDeferred.await(), SportSource.GIOVANG, nowEpochMs)
            enrichments += parseGenericEnrichment(giovangLiveDeferred.await(), SportSource.GIOVANG, nowEpochMs)

            mergeEnrichments(backbone, enrichments)
        }

        if (result.isNotEmpty()) {
            cachedMatches = result
            lastFetchMs = nowEpochMs
        }
        return result
    }

    fun clearMemoryCache() {
        cachedMatches = emptyList()
        lastFetchMs = 0L
    }

    internal fun parseSocolive(
        recommendJson: String?,
        liveRoomsJson: String?,
        nowEpochMs: Long
    ): List<MatchModel> {
        val byKey = LinkedHashMap<String, MatchModel>()

        fun consumeArray(arr: JSONArray?, fromLiveEndpoint: Boolean) {
            if (arr == null) return
            for (i in 0 until arr.length()) {
                val obj = arr.optJSONObject(i) ?: continue
                val id = obj.optString("matchId").ifBlank {
                    obj.optString("id").ifBlank { "soco_${i}_${obj.optString("hostName")}" }
                }
                val home = obj.optString("hostName").ifBlank {
                    obj.optString("homeName").ifBlank { obj.optString("home_team") }
                }.trim()
                val away = obj.optString("guestName").ifBlank {
                    obj.optString("awayName").ifBlank { obj.optString("away_team") }
                }.trim()
                if (home.isBlank() || away.isBlank()) continue

                val kickoff = TimeUtils.parseIsoOrEpoch(
                    obj.opt("matchTime") ?: obj.opt("startTime") ?: obj.opt("kickoff")
                )
                val statusRaw = obj.optString("status").lowercase()
                val explicitlyFinished = statusRaw in setOf("ft", "finished", "ended", "3")
                val explicitlyLive = fromLiveEndpoint || obj.optBoolean("isLive", false) ||
                    statusRaw in setOf("live", "1", "playing", "ht")

                val state = TimeUtils.computeMatchState(
                    kickoffEpochMs = kickoff,
                    nowEpochMs = nowEpochMs,
                    isExplicitlyLive = explicitlyLive,
                    isExplicitlyFinished = explicitlyFinished
                )

                val roomTitle = obj.optString("title").ifBlank { obj.optString("roomTitle") }
                val numericScores = ScoreParser.parseNumericScores(
                    obj.opt("hostScore") ?: obj.opt("homeScore"),
                    obj.opt("guestScore") ?: obj.opt("awayScore"),
                    state
                )
                val resolved = ScoreParser.resolveHeroScore(
                    numericScores.hostScore,
                    numericScores.guestScore,
                    roomTitle,
                    state
                )

                val streamUrl = obj.optString("m3u8").ifBlank {
                    obj.optString("playUrl").ifBlank { obj.optString("streamUrl") }
                }
                val commentator = obj.optString("anchorName").ifBlank {
                    obj.optString("commentator").ifBlank { "BLV Socolive" }
                }
                val views = obj.optInt("viewCount", obj.optInt("hot", 0))
                val newStreams = if (streamUrl.isNotBlank()) {
                    listOf(
                        StreamSource(
                            source = SportSource.SOCOLIVE,
                            label = "Socolive · $commentator",
                            streamUrl = streamUrl,
                            commentator = commentator,
                            viewCount = views
                        )
                    )
                } else emptyList()

                val existing = byKey[id]
                if (existing == null) {
                    byKey[id] = MatchModel(
                        id = id,
                        homeTeam = home,
                        awayTeam = away,
                        homeLogo = normalizeLogo(obj.optString("hostIcon").ifBlank { obj.optString("homeLogo") }),
                        awayLogo = normalizeLogo(obj.optString("guestIcon").ifBlank { obj.optString("awayLogo") }),
                        leagueName = obj.optString("leagueName").ifBlank { obj.optString("league") },
                        kickoffEpochMs = kickoff,
                        state = state,
                        hostScore = resolved.hostScore,
                        guestScore = resolved.guestScore,
                        minuteText = obj.optString("minute").ifBlank { null },
                        commentator = commentator,
                        viewCount = views,
                        isFeatured = obj.optBoolean("isHot", false) || obj.optBoolean("featured", false),
                        sportType = obj.optString("sportType", "football").ifBlank { "football" },
                        streams = newStreams
                    )
                } else {
                    // Merge extra live room streams into existing match
                    val mergedStreams = (existing.streams + newStreams).distinctBy { it.streamUrl }
                    byKey[id] = existing.copy(
                        state = if (state == MatchState.LIVE) MatchState.LIVE else existing.state,
                        hostScore = existing.hostScore ?: resolved.hostScore,
                        guestScore = existing.guestScore ?: resolved.guestScore,
                        viewCount = maxOf(existing.viewCount, views),
                        streams = mergedStreams
                    )
                }
            }
        }

        extractDataArray(liveRoomsJson)?.let { consumeArray(it, true) }
        extractDataArray(recommendJson)?.let { consumeArray(it, false) }

        return byKey.values.sortedWith(
            compareBy<MatchModel> {
                when (it.state) {
                    MatchState.LIVE -> 0
                    MatchState.UPCOMING -> 1
                    MatchState.FINISHED -> 2
                }
            }.thenByDescending { it.isFeatured }.thenBy { it.kickoffEpochMs }
        )
    }

    internal fun parseGenericEnrichment(
        rawJson: String?,
        source: SportSource,
        nowEpochMs: Long
    ): List<EnrichmentData> {
        val arr = extractDataArray(rawJson) ?: return emptyList()
        val list = mutableListOf<EnrichmentData>()
        for (i in 0 until arr.length()) {
            val obj = arr.optJSONObject(i) ?: continue
            val homeObj = obj.optJSONObject("home") ?: obj.optJSONObject("homeTeam")
            val awayObj = obj.optJSONObject("away") ?: obj.optJSONObject("awayTeam")

            val homeName = homeObj?.optString("name")?.ifBlank { null }
                ?: obj.optString("homeName").ifBlank { obj.optString("home_team") }
            val awayName = awayObj?.optString("name")?.ifBlank { null }
                ?: obj.optString("awayName").ifBlank { obj.optString("away_team") }
            if (homeName.isBlank() || awayName.isBlank()) continue

            val kickoff = TimeUtils.parseIsoOrEpoch(
                obj.opt("timestamp") ?: obj.opt("startTime") ?: obj.opt("kickoff") ?: obj.opt("matchTime")
            )
            val statusStr = obj.optString("status").lowercase()
            val isFinished = statusStr in setOf("ft", "finished", "ended")
            val isLive = obj.optBoolean("isLive", false) || statusStr in setOf("live", "playing", "ht")
            val state = TimeUtils.computeMatchState(kickoff, nowEpochMs, isLive, isFinished)

            val scoresObj = obj.optJSONObject("scores")
            val parsedScore = ScoreParser.parseNumericScores(
                homeObj?.opt("score") ?: scoresObj?.opt("home") ?: obj.opt("homeScore") ?: obj.opt("hostScore"),
                awayObj?.opt("score") ?: scoresObj?.opt("away") ?: obj.opt("awayScore") ?: obj.opt("guestScore"),
                state
            )

            val playUrls = obj.optJSONArray("playUrls")
            val streamUrl = obj.optString("m3u8").ifBlank {
                obj.optString("streamUrl").ifBlank {
                    obj.optString("playUrl").ifBlank {
                        playUrls?.optJSONObject(0)?.optString("url") ?: ""
                    }
                }
            }
            val stream = if (streamUrl.isNotBlank()) {
                StreamSource(
                    source = source,
                    label = source.displayName,
                    streamUrl = streamUrl,
                    commentator = obj.optString("commentator")
                )
            } else null

            list.add(
                EnrichmentData(
                    homeTeam = homeName.trim(),
                    awayTeam = awayName.trim(),
                    kickoffEpochMs = kickoff,
                    homeLogo = normalizeLogo(homeObj?.optString("logo") ?: obj.optString("homeLogo")),
                    awayLogo = normalizeLogo(awayObj?.optString("logo") ?: obj.optString("awayLogo")),
                    hostScore = parsedScore.hostScore,
                    guestScore = parsedScore.guestScore,
                    minuteText = obj.optString("minute").ifBlank { null },
                    isLive = state == MatchState.LIVE,
                    isFinished = state == MatchState.FINISHED,
                    stream = stream
                )
            )
        }
        return list
    }

    internal fun mergeEnrichments(
        backbone: MutableList<MatchModel>,
        enrichments: List<EnrichmentData>
    ): List<MatchModel> {
        return backbone.map { match ->
            val matched = enrichments.filter { e ->
                TeamNameMatcher.isSameMatch(
                    match.homeTeam, match.awayTeam, match.kickoffEpochMs,
                    e.homeTeam, e.awayTeam, e.kickoffEpochMs
                )
            }
            if (matched.isEmpty()) {
                match
            } else {
                var hostScore = match.hostScore
                var guestScore = match.guestScore
                var homeLogo = match.homeLogo
                var awayLogo = match.awayLogo
                var minute = match.minuteText
                val extraStreams = match.streams.toMutableList()

                for (e in matched) {
                    if (match.state != MatchState.UPCOMING) {
                        if (hostScore == null && e.hostScore != null) hostScore = e.hostScore
                        if (guestScore == null && e.guestScore != null) guestScore = e.guestScore
                    }
                    if (homeLogo.isNullOrBlank() && !e.homeLogo.isNullOrBlank()) homeLogo = e.homeLogo
                    if (awayLogo.isNullOrBlank() && !e.awayLogo.isNullOrBlank()) awayLogo = e.awayLogo
                    if (minute.isNullOrBlank() && !e.minuteText.isNullOrBlank()) minute = e.minuteText
                    if (e.stream != null && extraStreams.none { it.streamUrl == e.stream.streamUrl }) {
                        extraStreams.add(e.stream)
                    }
                }

                match.copy(
                    homeLogo = homeLogo,
                    awayLogo = awayLogo,
                    hostScore = hostScore,
                    guestScore = guestScore,
                    minuteText = minute,
                    streams = extraStreams
                )
            }
        }
    }

    private fun normalizeLogo(raw: String?): String? {
        val s = raw?.trim() ?: return null
        if (s.isEmpty() || s == "null") return null
        return if (s.startsWith("http")) s else "$ESPN_LOGO_BASE$s"
    }

    private fun extractDataArray(rawJson: String?): JSONArray? {
        if (rawJson.isNullOrBlank()) return null
        val trimmed = rawJson.trim()
        return runCatching {
            if (trimmed.startsWith("[")) {
                JSONArray(trimmed)
            } else {
                val obj = JSONObject(trimmed)
                obj.optJSONArray("data")
                    ?: obj.optJSONArray("matches")
                    ?: obj.optJSONArray("list")
                    ?: obj.optJSONArray("items")
                    ?: obj.optJSONObject("data")?.optJSONArray("list")
            }
        }.getOrNull()
    }
}
