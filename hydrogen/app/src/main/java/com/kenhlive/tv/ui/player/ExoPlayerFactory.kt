package com.kenhlive.tv.ui.player

import android.content.Context
import androidx.media3.exoplayer.DefaultLoadControl
import androidx.media3.exoplayer.ExoPlayer

object ExoPlayerFactory {
    /**
     * Builds an ExoPlayer tuned for older Android TVs (low RAM, fast initial buffer).
     */
    fun create(context: Context): ExoPlayer {
        val loadControl = DefaultLoadControl.Builder()
            .setBufferDurationsMs(
                15_000,
                30_000,
                1_800,
                3_500
            )
            .setPrioritizeTimeOverSizeThresholds(true)
            .build()

        return ExoPlayer.Builder(context)
            .setLoadControl(loadControl)
            .build()
    }
}
