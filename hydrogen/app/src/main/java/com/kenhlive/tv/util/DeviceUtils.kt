package com.kenhlive.tv.util

import android.app.UiModeManager
import android.content.Context
import android.content.res.Configuration

object DeviceUtils {
    fun isTv(context: Context): Boolean {
        val uiModeManager = context.getSystemService(Context.UI_MODE_SERVICE) as? UiModeManager
        return uiModeManager?.currentModeType == Configuration.UI_MODE_TYPE_TELEVISION
    }

    fun isPhone(context: Context): Boolean = !isTv(context)
}
