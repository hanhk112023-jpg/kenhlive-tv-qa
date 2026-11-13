package com.kenhlive.tv.repository

import com.kenhlive.tv.model.MovieDetail
import com.kenhlive.tv.model.MovieEpisode
import com.kenhlive.tv.model.MovieItem
import com.kenhlive.tv.model.MovieServer
import com.kenhlive.tv.network.HttpClientProvider
import org.json.JSONObject

class MovieRepository {

    companion object {
        private const val KKPHIM_NEW_URL = "https://phimapi.com/v1/api/danh-sach/phim-moi-cap-nhat"
        private const val KKPHIM_BASE = "https://phimapi.com"
        private const val KKPHIM_IMG_BASE = "https://phimimg.com/"
        const val KKPHIM_PLAYER_BASE = "https://player.phimapi.com/player/"
    }

    suspend fun fetchLatestMovies(page: Int = 1): List<MovieItem> {
        val raw = HttpClientProvider.getString("$KKPHIM_NEW_URL?page=$page") ?: return emptyList()
        return parseMovieList(raw)
    }

    suspend fun searchMovies(keyword: String): List<MovieItem> {
        val encoded = java.net.URLEncoder.encode(keyword, "UTF-8")
        val raw = HttpClientProvider.getString("$KKPHIM_BASE/v1/api/tim-kiem?keyword=$encoded&limit=24")
            ?: return emptyList()
        return parseMovieList(raw)
    }

    suspend fun fetchMovieDetail(slug: String): MovieDetail? {
        val raw = HttpClientProvider.getString("$KKPHIM_BASE/phim/$slug") ?: return null
        return runCatching {
            val root = JSONObject(raw)
            val movie = root.optJSONObject("movie") ?: return null
            val categories = mutableListOf<String>()
            val catArr = movie.optJSONArray("category")
            if (catArr != null) {
                for (i in 0 until catArr.length()) {
                    catArr.optJSONObject(i)?.optString("name")?.takeIf { it.isNotBlank() }?.let { categories.add(it) }
                }
            }
            val countries = mutableListOf<String>()
            val countryArr = movie.optJSONArray("country")
            if (countryArr != null) {
                for (i in 0 until countryArr.length()) {
                    countryArr.optJSONObject(i)?.optString("name")?.takeIf { it.isNotBlank() }?.let { countries.add(it) }
                }
            }

            val servers = mutableListOf<MovieServer>()
            val epArr = root.optJSONArray("episodes")
            if (epArr != null) {
                for (i in 0 until epArr.length()) {
                    val srv = epArr.optJSONObject(i) ?: continue
                    val srvName = srv.optString("server_name", "Server ${i + 1}")
                    val dataArr = srv.optJSONArray("server_data") ?: continue
                    val episodes = mutableListOf<MovieEpisode>()
                    for (j in 0 until dataArr.length()) {
                        val ep = dataArr.optJSONObject(j) ?: continue
                        val m3u8 = ep.optString("link_m3u8")
                        val embed = ep.optString("link_embed")
                        episodes.add(
                            MovieEpisode(
                                name = ep.optString("name", "Tập ${j + 1}"),
                                slug = ep.optString("slug"),
                                linkEmbed = embed.ifBlank {
                                    if (m3u8.isNotBlank()) "$KKPHIM_PLAYER_BASE?url=$m3u8" else ""
                                },
                                linkM3u8 = m3u8
                            )
                        )
                    }
                    if (episodes.isNotEmpty()) {
                        servers.add(MovieServer(srvName, episodes))
                    }
                }
            }

            MovieDetail(
                id = movie.optString("_id"),
                name = movie.optString("name"),
                originName = movie.optString("origin_name"),
                slug = movie.optString("slug"),
                content = movie.optString("content").replace(Regex("<[^>]*>"), "").trim(),
                posterUrl = normalizeImageUrl(movie.optString("poster_url")),
                thumbUrl = normalizeImageUrl(movie.optString("thumb_url")),
                year = movie.optInt("year", 0),
                time = movie.optString("time"),
                quality = movie.optString("quality"),
                lang = movie.optString("lang"),
                categories = categories,
                countries = countries,
                servers = servers
            )
        }.getOrNull()
    }

    private fun parseMovieList(raw: String): List<MovieItem> {
        return runCatching {
            val root = JSONObject(raw)
            val dataObj = root.optJSONObject("data")
            val items = dataObj?.optJSONArray("items") ?: root.optJSONArray("items") ?: return emptyList()
            val list = mutableListOf<MovieItem>()
            for (i in 0 until items.length()) {
                val obj = items.optJSONObject(i) ?: continue
                list.add(
                    MovieItem(
                        id = obj.optString("_id"),
                        name = obj.optString("name"),
                        originName = obj.optString("origin_name"),
                        slug = obj.optString("slug"),
                        posterUrl = normalizeImageUrl(obj.optString("poster_url")),
                        thumbUrl = normalizeImageUrl(obj.optString("thumb_url")),
                        year = obj.optInt("year", 0),
                        quality = obj.optString("quality"),
                        lang = obj.optString("lang"),
                        episodeCurrent = obj.optString("episode_current")
                    )
                )
            }
            list
        }.getOrElse { emptyList() }
    }

    private fun normalizeImageUrl(url: String): String {
        if (url.isBlank()) return ""
        return if (url.startsWith("http")) url else KKPHIM_IMG_BASE + url.trimStart('/')
    }
}
