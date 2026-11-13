package com.kenhlive.tv

import android.app.Application
import coil.ImageLoader
import coil.ImageLoaderFactory
import coil.disk.DiskCache
import coil.memory.MemoryCache
import com.kenhlive.tv.network.HttpClientProvider

class KenhLiveApp : Application(), ImageLoaderFactory {
    override fun onCreate() {
        super.onCreate()
        HttpClientProvider.init(this)
    }

    /**
     * Tuned for older Android TVs (1GB-1.5GB RAM, minSdk 21):
     * caps memory cache at 18% and disk cache at 40MB to prevent OOM & GC jank.
     */
    override fun newImageLoader(): ImageLoader {
        return ImageLoader.Builder(this)
            .okHttpClient { HttpClientProvider.getClient() }
            .memoryCache {
                MemoryCache.Builder(this)
                    .maxSizePercent(0.18)
                    .build()
            }
            .diskCache {
                DiskCache.Builder()
                    .directory(cacheDir.resolve("coil_image_cache"))
                    .maxSizeBytes(40L * 1024L * 1024L)
                    .build()
            }
            .crossfade(120)
            .respectCacheHeaders(false)
            .build()
    }
}
