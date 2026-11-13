package com.kenhlive.tv.repository

import com.kenhlive.tv.model.EpgProgram
import com.kenhlive.tv.model.IptvChannel
import com.kenhlive.tv.network.HttpClientProvider
import kotlinx.coroutines.async
import kotlinx.coroutines.coroutineScope
import org.json.JSONObject
import org.xmlpull.v1.XmlPullParser
import org.xmlpull.v1.XmlPullParserFactory
import java.io.ByteArrayInputStream
import java.io.InputStreamReader
import java.text.SimpleDateFormat
import java.util.Locale
import java.util.zip.GZIPInputStream

class IptvRepository {

    companion object {
        private val PLAYLIST_URLS = listOf(
            "https://thtt.pages.dev/tttt.m3u",
            "https://iptv-org.github.io/iptv/countries/vn.m3u",
            "https://iptv-org.github.io/iptv/categories/sports.m3u"
        )
        private const val EPG_URL = "https://epgshare01.online/epgshare01/epg_ripper_VN1.xml.gz"
        const val TV360_GET_LINK_PREFIX = "https://tv360.vn/public/v1/composite/get-link"
        private const val CACHE_TTL_MS = 10L * 60L * 1000L
    }

    @Volatile
    private var cachedChannels: List<IptvChannel> = emptyList()
    @Volatile
    private var cachedEpg: Map<String, EpgProgram> = emptyMap()
    @Volatile
    private var lastFetchMs: Long = 0L

    suspend fun fetchChannels(forceRefresh: Boolean = false): List<IptvChannel> {
        val now = System.currentTimeMillis()
        if (!forceRefresh && cachedChannels.isNotEmpty() && (now - lastFetchMs) < CACHE_TTL_MS) {
            return cachedChannels
        }
        val merged = coroutineScope {
            val results = PLAYLIST_URLS.map { url ->
                async { runCatching { HttpClientProvider.getString(url)?.let { parseM3u(it) } }.getOrNull() ?: emptyList() }
            }
            val list = mutableListOf<IptvChannel>()
            val seenUrls = HashSet<String>()
            for (deferred in results) {
                for (ch in deferred.await()) {
                    if (seenUrls.add(ch.streamUrl)) {
                        list.add(ch)
                    }
                }
            }
            list
        }
        if (merged.isNotEmpty()) {
            cachedChannels = merged
            lastFetchMs = now
        }
        return merged
    }

    suspend fun fetchCurrentEpgMap(nowEpochMs: Long = System.currentTimeMillis()): Map<String, EpgProgram> {
        if (cachedEpg.isNotEmpty() && (nowEpochMs - lastFetchMs) < CACHE_TTL_MS) {
            return cachedEpg
        }
        val gzBytes = HttpClientProvider.getBytes(EPG_URL) ?: return emptyMap()
        val parsed = runCatching {
            val map = HashMap<String, EpgProgram>()
            GZIPInputStream(ByteArrayInputStream(gzBytes)).use { gzip ->
                val factory = XmlPullParserFactory.newInstance()
                val parser = factory.newPullParser()
                parser.setInput(InputStreamReader(gzip, Charsets.UTF_8))

                var eventType = parser.eventType
                var currentChannel = ""
                var currentStart = 0L
                var currentStop = 0L
                var currentTitle = ""
                var inProgramme = false

                while (eventType != XmlPullParser.END_DOCUMENT) {
                    when (eventType) {
                        XmlPullParser.START_TAG -> {
                            when (parser.name) {
                                "programme" -> {
                                    inProgramme = true
                                    currentChannel = parser.getAttributeValue(null, "channel") ?: ""
                                    currentStart = parseEpgTime(parser.getAttributeValue(null, "start"))
                                    currentStop = parseEpgTime(parser.getAttributeValue(null, "stop"))
                                    currentTitle = ""
                                }
                                "title" -> if (inProgramme) {
                                    currentTitle = parser.nextText().trim()
                                }
                            }
                        }
                        XmlPullParser.END_TAG -> {
                            if (parser.name == "programme" && inProgramme) {
                                if (currentChannel.isNotBlank() &&
                                    currentTitle.isNotBlank() &&
                                    nowEpochMs in currentStart..currentStop
                                ) {
                                    map[currentChannel] = EpgProgram(
                                        channelId = currentChannel,
                                        title = currentTitle,
                                        startEpochMs = currentStart,
                                        endEpochMs = currentStop
                                    )
                                }
                                inProgramme = false
                            }
                        }
                    }
                    eventType = parser.next()
                }
            }
            map
        }.getOrElse { emptyMap() }
        if (parsed.isNotEmpty()) cachedEpg = parsed
        return parsed
    }

    /**
     * Resolves tv360.vn/public/v1/composite/get-link JSON wrapper to actual .m3u8 URL if needed.
     */
    suspend fun resolvePlayableStreamUrl(rawUrl: String): String {
        if (!rawUrl.startsWith(TV360_GET_LINK_PREFIX)) return rawUrl
        val json = HttpClientProvider.getString(rawUrl) ?: return rawUrl
        return runCatching {
            val obj = JSONObject(json)
            obj.optJSONObject("data")?.optString("url")?.ifBlank { null }
                ?: obj.optString("url").ifBlank { rawUrl }
        }.getOrDefault(rawUrl)
    }

    internal fun parseM3u(content: String): List<IptvChannel> {
        val channels = mutableListOf<IptvChannel>()
        val lines = content.lines()
        var pendingName = ""
        var pendingGroup = "Tổng hợp"
        var pendingLogo: String? = null
        var pendingTvgId = ""

        val tvgIdRegex = Regex("""tvg-id="([^"]*)"""")
        val tvgLogoRegex = Regex("""tvg-logo="([^"]*)"""")
        val groupRegex = Regex("""group-title="([^"]*)"""")

        for (rawLine in lines) {
            val line = rawLine.trim()
            if (line.isEmpty()) continue
            if (line.startsWith("#EXTINF:")) {
                pendingTvgId = tvgIdRegex.find(line)?.groupValues?.get(1) ?: ""
                pendingLogo = tvgLogoRegex.find(line)?.groupValues?.get(1)?.ifBlank { null }
                pendingGroup = groupRegex.find(line)?.groupValues?.get(1)?.ifBlank { "Tổng hợp" } ?: "Tổng hợp"
                pendingName = line.substringAfterLast(",", "").trim()
            } else if (!line.startsWith("#")) {
                if (pendingName.isNotBlank()) {
                    channels.add(
                        IptvChannel(
                            id = "${pendingName.hashCode()}_${line.hashCode()}",
                            name = pendingName,
                            groupTitle = pendingGroup,
                            logoUrl = pendingLogo,
                            streamUrl = line,
                            tvgId = pendingTvgId,
                            isGeoBlockedSuspected = line.contains("tv360.vn") || line.contains("vtvcab")
                        )
                    )
                }
                pendingName = ""
                pendingLogo = null
                pendingTvgId = ""
            }
        }
        return channels
    }

    private fun parseEpgTime(raw: String?): Long {
        if (raw.isNullOrBlank()) return 0L
        return runCatching {
            val sdf = SimpleDateFormat("yyyyMMddHHmmss Z", Locale.US)
            sdf.parse(raw.trim())?.time ?: 0L
        }.getOrDefault(0L)
    }
}
