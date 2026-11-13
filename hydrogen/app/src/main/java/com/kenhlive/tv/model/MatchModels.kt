package com.kenhlive.tv.model

enum class MatchState {
    UPCOMING,
    LIVE,
    FINISHED
}

enum class SportSource(val displayName: String) {
    SOCOLIVE("Socolive"),
    COLATV("ColaTV"),
    GAVANG("Gà Vàng"),
    GIOVANG("Giờ Vàng")
}

data class StreamSource(
    val source: SportSource,
    val label: String,
    val streamUrl: String,
    val commentator: String = "",
    val viewCount: Int = 0
)

data class MatchModel(
    val id: String,
    val homeTeam: String,
    val awayTeam: String,
    val homeLogo: String? = null,
    val awayLogo: String? = null,
    val leagueName: String = "",
    val kickoffEpochMs: Long,
    val state: MatchState,
    val hostScore: Int? = null,
    val guestScore: Int? = null,
    val minuteText: String? = null,
    val commentator: String = "",
    val viewCount: Int = 0,
    val isFeatured: Boolean = false,
    val sportType: String = "football",
    val streams: List<StreamSource> = emptyList()
) {
    fun hasRealScore(): Boolean =
        state != MatchState.UPCOMING && hostScore != null && guestScore != null

    fun displayScoreOrVs(): String {
        return if (hasRealScore()) {
            "$hostScore : $guestScore"
        } else {
            "VS"
        }
    }
}
