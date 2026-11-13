package com.kenhlive.tv.logic

import com.kenhlive.tv.model.MatchState
import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Date
import java.util.Locale
import java.util.TimeZone

object TimeUtils {
    val VN_TIMEZONE: TimeZone = TimeZone.getTimeZone("Asia/Ho_Chi_Minh")
    private const val TWO_HOURS_FORTY_MIN_MS = 160L * 60L * 1000L
    private const val PRE_KICKOFF_LIVE_WINDOW_MS = 10L * 60L * 1000L

    fun computeMatchState(
        kickoffEpochMs: Long,
        nowEpochMs: Long = System.currentTimeMillis(),
        isExplicitlyLive: Boolean = false,
        isExplicitlyFinished: Boolean = false,
        maxDurationMs: Long = TWO_HOURS_FORTY_MIN_MS
    ): MatchState {
        if (isExplicitlyFinished) return MatchState.FINISHED
        if (kickoffEpochMs <= 0L) {
            return if (isExplicitlyLive) MatchState.LIVE else MatchState.UPCOMING
        }
        val diff = nowEpochMs - kickoffEpochMs
        return when {
            diff < -PRE_KICKOFF_LIVE_WINDOW_MS -> MatchState.UPCOMING
            diff < 0L -> if (isExplicitlyLive) MatchState.LIVE else MatchState.UPCOMING
            diff <= maxDurationMs -> MatchState.LIVE
            else -> if (isExplicitlyLive && diff <= maxDurationMs + 30L * 60L * 1000L) {
                MatchState.LIVE
            } else {
                MatchState.FINISHED
            }
        }
    }

    fun formatKickoffTime(epochMs: Long): String {
        if (epochMs <= 0L) return "--:--"
        val sdf = SimpleDateFormat("HH:mm", Locale.getDefault()).apply {
            timeZone = VN_TIMEZONE
        }
        return sdf.format(Date(epochMs))
    }

    fun formatKickoffShortDateTime(epochMs: Long): String {
        if (epochMs <= 0L) return "--:--"
        val sdf = SimpleDateFormat("HH:mm · dd/MM", Locale.getDefault()).apply {
            timeZone = VN_TIMEZONE
        }
        return sdf.format(Date(epochMs))
    }

    fun formatDayHeader(epochMs: Long, nowEpochMs: Long = System.currentTimeMillis()): String {
        val calTarget = Calendar.getInstance(VN_TIMEZONE).apply { timeInMillis = epochMs }
        val calNow = Calendar.getInstance(VN_TIMEZONE).apply { timeInMillis = nowEpochMs }

        val targetDay = calTarget.get(Calendar.YEAR) * 1000 + calTarget.get(Calendar.DAY_OF_YEAR)
        val nowDay = calNow.get(Calendar.YEAR) * 1000 + calNow.get(Calendar.DAY_OF_YEAR)

        val dateSdf = SimpleDateFormat("dd/MM/yyyy", Locale("vi", "VN")).apply {
            timeZone = VN_TIMEZONE
        }
        val dateStr = dateSdf.format(Date(epochMs))

        return when (targetDay - nowDay) {
            0 -> "Hôm nay · $dateStr"
            1 -> "Ngày mai · $dateStr"
            -1 -> "Hôm qua · $dateStr"
            else -> {
                val dayOfWeek = when (calTarget.get(Calendar.DAY_OF_WEEK)) {
                    Calendar.MONDAY -> "Thứ 2"
                    Calendar.TUESDAY -> "Thứ 3"
                    Calendar.WEDNESDAY -> "Thứ 4"
                    Calendar.THURSDAY -> "Thứ 5"
                    Calendar.FRIDAY -> "Thứ 6"
                    Calendar.SATURDAY -> "Thứ 7"
                    Calendar.SUNDAY -> "Chủ nhật"
                    else -> ""
                }
                "$dayOfWeek · $dateStr"
            }
        }
    }

    fun dayKey(epochMs: Long): String {
        val sdf = SimpleDateFormat("yyyy-MM-dd", Locale.US).apply {
            timeZone = VN_TIMEZONE
        }
        return sdf.format(Date(epochMs))
    }

    fun parseIsoOrEpoch(raw: Any?): Long {
        if (raw == null) return 0L
        if (raw is Number) {
            val v = raw.toLong()
            return if (v in 1L..9_999_999_999L) v * 1000L else v
        }
        val s = raw.toString().trim()
        if (s.isEmpty()) return 0L
        s.toLongOrNull()?.let { v ->
            return if (v in 1L..9_999_999_999L) v * 1000L else v
        }
        val patterns = listOf(
            "yyyy-MM-dd'T'HH:mm:ss.SSS'Z'",
            "yyyy-MM-dd'T'HH:mm:ss'Z'",
            "yyyy-MM-dd'T'HH:mm:ssXXX",
            "yyyy-MM-dd HH:mm:ss",
            "yyyy-MM-dd HH:mm"
        )
        for (p in patterns) {
            try {
                val sdf = SimpleDateFormat(p, Locale.US).apply {
                    timeZone = if (p.endsWith("'Z'")) TimeZone.getTimeZone("UTC") else VN_TIMEZONE
                }
                val parsed = sdf.parse(s)
                if (parsed != null) return parsed.time
            } catch (_: Exception) {
            }
        }
        return 0L
    }
}
