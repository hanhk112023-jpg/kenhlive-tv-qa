package com.kenhlive.tv.util

import android.view.View

object TvFocusHelper {
    private const val SCALE_FOCUSED = 1.06f
    private const val SCALE_DEFAULT = 1.0f
    private const val DURATION_MS = 180L

    fun attachFocusScale(view: View) {
        view.setOnFocusChangeListener { v, hasFocus ->
            val target = if (hasFocus) SCALE_FOCUSED else SCALE_DEFAULT
            v.animate()
                .scaleX(target)
                .scaleY(target)
                .setDuration(DURATION_MS)
                .start()
            v.elevation = if (hasFocus) 12f else 2f
        }
    }
}
