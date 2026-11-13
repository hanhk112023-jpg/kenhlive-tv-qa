package com.kenhlive.tv.network

import android.content.Context
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.Cache
import okhttp3.OkHttpClient
import okhttp3.Request
import java.io.File
import java.util.concurrent.TimeUnit

object HttpClientProvider {
    @Volatile
    private var client: OkHttpClient? = null
    private var cacheDir: File? = null

    fun init(context: Context) {
        if (client == null) {
            synchronized(this) {
                if (client == null) {
                    val dir = File(context.cacheDir, "http_cache")
                    cacheDir = dir
                    client = OkHttpClient.Builder()
                        .cache(Cache(dir, 20L * 1024L * 1024L))
                        .connectTimeout(12, TimeUnit.SECONDS)
                        .readTimeout(15, TimeUnit.SECONDS)
                        .followRedirects(true)
                        .build()
                }
            }
        }
    }

    fun getClient(): OkHttpClient {
        return client ?: OkHttpClient.Builder()
            .connectTimeout(12, TimeUnit.SECONDS)
            .readTimeout(15, TimeUnit.SECONDS)
            .followRedirects(true)
            .build()
    }

    suspend fun getString(url: String, headers: Map<String, String> = emptyMap()): String? =
        withContext(Dispatchers.IO) {
            runCatching {
                val builder = Request.Builder()
                    .url(url)
                    .header("User-Agent", "KenhLive/0.1.12 (Android)")
                headers.forEach { (k, v) -> builder.header(k, v) }
                getClient().newCall(builder.build()).execute().use { resp ->
                    if (!resp.isSuccessful) return@use null
                    resp.body?.string()
                }
            }.getOrNull()
        }

    suspend fun getBytes(url: String): ByteArray? = withContext(Dispatchers.IO) {
        runCatching {
            val req = Request.Builder()
                .url(url)
                .header("User-Agent", "KenhLive/0.1.12 (Android)")
                .build()
            getClient().newCall(req).execute().use { resp ->
                if (!resp.isSuccessful) return@use null
                resp.body?.bytes()
            }
        }.getOrNull()
    }

    fun clearCache() {
        runCatching { client?.cache?.evictAll() }
        runCatching { cacheDir?.deleteRecursively() }
    }
}
