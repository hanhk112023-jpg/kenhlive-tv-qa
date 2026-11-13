package com.kenhlive.tv.ui.schedule

import android.view.KeyEvent
import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.core.content.ContextCompat
import androidx.recyclerview.widget.RecyclerView
import com.kenhlive.tv.R
import com.kenhlive.tv.databinding.ItemScheduleDayHeaderBinding
import com.kenhlive.tv.databinding.ItemScheduleRowBinding
import com.kenhlive.tv.logic.TimeUtils
import com.kenhlive.tv.model.MatchModel
import com.kenhlive.tv.model.MatchState
import com.kenhlive.tv.util.TvFocusHelper

sealed class ScheduleListItem {
    data class DayHeader(val title: String) : ScheduleListItem()
    data class MatchRow(val match: MatchModel) : ScheduleListItem()
}

class ScheduleAdapter(
    private val isTv: Boolean,
    private val onMatchClick: (MatchModel) -> Unit,
    private val onLeftDpad: () -> Unit
) : RecyclerView.Adapter<RecyclerView.ViewHolder>() {

    private val items = mutableListOf<ScheduleListItem>()

    fun submitMatches(matches: List<MatchModel>, nowEpochMs: Long = System.currentTimeMillis()) {
        items.clear()
        val sevenDaysLater = nowEpochMs + 7L * 24L * 3600L * 1000L
        val filtered = matches
            .filter { it.kickoffEpochMs in (nowEpochMs - 12L * 3600L * 1000L)..sevenDaysLater }
            .sortedBy { it.kickoffEpochMs }

        val grouped = filtered.groupBy { TimeUtils.dayKey(it.kickoffEpochMs) }
        for ((_, dayMatches) in grouped) {
            val firstTime = dayMatches.firstOrNull()?.kickoffEpochMs ?: continue
            items.add(ScheduleListItem.DayHeader(TimeUtils.formatDayHeader(firstTime, nowEpochMs)))
            dayMatches.forEach { items.add(ScheduleListItem.MatchRow(it)) }
        }
        notifyDataSetChanged()
    }

    override fun getItemViewType(position: Int): Int = when (items[position]) {
        is ScheduleListItem.DayHeader -> 0
        is ScheduleListItem.MatchRow -> 1
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): RecyclerView.ViewHolder {
        val inflater = LayoutInflater.from(parent.context)
        return if (viewType == 0) {
            HeaderVH(ItemScheduleDayHeaderBinding.inflate(inflater, parent, false))
        } else {
            RowVH(ItemScheduleRowBinding.inflate(inflater, parent, false))
        }
    }

    override fun onBindViewHolder(holder: RecyclerView.ViewHolder, position: Int) {
        when (val item = items[position]) {
            is ScheduleListItem.DayHeader -> (holder as HeaderVH).bind(item)
            is ScheduleListItem.MatchRow -> (holder as RowVH).bind(item.match)
        }
    }

    override fun getItemCount(): Int = items.size

    class HeaderVH(private val b: ItemScheduleDayHeaderBinding) : RecyclerView.ViewHolder(b.root) {
        fun bind(item: ScheduleListItem.DayHeader) {
            b.tvDayHeader.text = item.title
        }
    }

    inner class RowVH(private val b: ItemScheduleRowBinding) : RecyclerView.ViewHolder(b.root) {
        init {
            if (isTv) TvFocusHelper.attachFocusScale(b.root)
        }

        fun bind(match: MatchModel) {
            val ctx = b.root.context
            b.tvKickoff.text = TimeUtils.formatKickoffTime(match.kickoffEpochMs)
            b.tvMatchTitle.text = "${match.homeTeam} vs ${match.awayTeam}"

            if (match.state == MatchState.LIVE || match.state == MatchState.FINISHED) {
                b.tvScheduleScore.text = match.displayScoreOrVs()
                b.tvScheduleScore.setTextColor(
                    ContextCompat.getColor(
                        ctx,
                        if (match.state == MatchState.LIVE) R.color.kl3_score_live_gold else R.color.kl3_text_primary
                    )
                )
            } else {
                b.tvScheduleScore.text = ctx.getString(R.string.kl3_vs)
                b.tvScheduleScore.setTextColor(ContextCompat.getColor(ctx, R.color.kl3_text_secondary))
            }

            b.root.setOnClickListener { onMatchClick(match) }
            b.root.setOnKeyListener { _, keyCode, event ->
                if (isTv && event.action == KeyEvent.ACTION_DOWN && keyCode == KeyEvent.KEYCODE_DPAD_LEFT) {
                    onLeftDpad()
                    true
                } else {
                    false
                }
            }
        }
    }
}
