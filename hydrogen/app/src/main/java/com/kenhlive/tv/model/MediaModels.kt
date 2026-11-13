package com.kenhlive.tv.model

data class MovieItem(
    val id: String,
    val name: String,
    val originName: String,
    val slug: String,
    val posterUrl: String,
    val thumbUrl: String,
    val year: Int,
    val quality: String = "",
    val lang: String = "",
    val episodeCurrent: String = ""
)

data class MovieEpisode(
    val name: String,
    val slug: String,
    val linkEmbed: String,
    val linkM3u8: String
)

data class MovieServer(
    val serverName: String,
    val episodes: List<MovieEpisode>
)

data class MovieDetail(
    val id: String,
    val name: String,
    val originName: String,
    val slug: String,
    val content: String,
    val posterUrl: String,
    val thumbUrl: String,
    val year: Int,
    val time: String,
    val quality: String,
    val lang: String,
    val categories: List<String>,
    val countries: List<String>,
    val servers: List<MovieServer>
)

data class IptvChannel(
    val id: String,
    val name: String,
    val groupTitle: String,
    val logoUrl: String?,
    val streamUrl: String,
    val tvgId: String = "",
    val isGeoBlockedSuspected: Boolean = false
)

data class EpgProgram(
    val channelId: String,
    val title: String,
    val startEpochMs: Long,
    val endEpochMs: Long
)
