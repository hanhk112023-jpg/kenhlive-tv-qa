package com.kenhlive.tv.ui.sports

import android.view.KeyEvent
import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.core.content.ContextCompat
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import coil.load
import coil.size.Precision
import com.kenhlive.tv.R
import com.kenhlive.tv.databinding.ItemMatchCardBinding
import com.kenhlive.tv.logic.TimeUtils
import com.kenhlive.tv.model.MatchModel
import com.kenhlive.tv.model.MatchState
import com.kenhlive.tv.util.TvFocusHelper

class MatchCardAdapter(
    private val isTv: Boolean,
    private val spanCount: Int,
    private val onMatchClick: (MatchModel) -> Unit,
    private val onLeftEdgeDpadLeft: () -> Unit
) : ListAdapter<MatchModel, MatchCardAdapter.MatchVH>(MatchDiffCallback) {

    object MatchDiffCallback : DiffUtil.ItemCallback<MatchModel>() {
        override fun areItemsTheSame(oldItem: MatchModel, newItem: MatchModel): Boolean =
            oldItem.id == newItem.id

        override fun areContentsTheSame(oldItem: MatchModel, newItem: MatchModel): Boolean =
            oldItem == newItem
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): MatchVH {
        val binding = ItemMatchCardBinding.inflate(
            LayoutInflater.from(parent.context), parent, false
        )
        return MatchVH(binding)
    }

    override fun onBindViewHolder(holder: MatchVH, position: Int) {
        holder.bind(getItem(position), position)
    }

    inner class MatchVH(private val b: ItemMatchCardBinding) : RecyclerView.ViewHolder(b.root) {
        init {
            if (isTv) {
                TvFocusHelper.attachFocusScale(b.root)
            }
        }

        fun bind(match: MatchModel, position: Int) {
            val ctx = b.root.context
            b.tvHomeTeam.text = match.homeTeam
            b.tvAwayTeam.text = match.awayTeam
            b.tvLeagueName.text = match.leagueName

            b.ivHomeLogo.load(match.homeLogo) {
                size(84, 84)
                precision(Precision.INEXACT)
                crossfade(true)
            }
            b.ivAwayLogo.load(match.awayLogo) {
                size(84, 84)
                precision(Precision.INEXACT)
                crossfade(true)
            }

            when (match.state) {
                MatchState.LIVE -> {
                    b.tvStateBadge.text = ctx.getString(R.string.kl3_badge_live)
                    b.tvStateBadge.setBackgroundResource(R.drawable.kl3_badge_live)
                    b.tvRightCorner.text = match.minuteText ?: "LIVE"
                    b.tvCenterScore.text = match.displayScoreOrVs()
                    b.tvCenterScore.setTextColor(
                        ContextCompat.getColor(ctx, R.color.kl3_score_live_gold)
                    )
                }
                MatchState.FINISHED -> {
                    b.tvStateBadge.text = ctx.getString(R.string.kl3_badge_finished)
                    b.tvStateBadge.setBackgroundResource(R.drawable.kl3_badge_finished)
                    b.tvRightCorner.text = TimeUtils.formatKickoffTime(match.kickoffEpochMs)
                    b.tvCenterScore.text = match.displayScoreOrVs()
                    b.tvCenterScore.setTextColor(
                        ContextCompat.getColor(ctx, R.color.kl3_text_primary)
                    )
                }
                MatchState.UPCOMING -> {
                    b.tvStateBadge.text = ctx.getString(R.string.kl3_badge_upcoming)
                    b.tvStateBadge.setBackgroundResource(R.drawable.kl3_badge_upcoming)
                    b.tvRightCorner.text = TimeUtils.formatKickoffShortDateTime(match.kickoffEpochMs)
                    b.tvCenterScore.text = ctx.getString(R.string.kl3_vs)
                    b.tvCenterScore.setTextColor(
                        ContextCompat.getColor(ctx, R.color.kl3_text_secondary)
                    )
                }
            }

            val kickoffStr = TimeUtils.formatKickoffTime(match.kickoffEpochMs)
            val viewsStr = if (match.viewCount > 0) " · ${match.viewCount} lượt xem" else ""
            val blvStr = if (match.commentator.isNotBlank()) "${match.commentator} · " else ""
            b.tvBottomMeta.text = "$blvStr$kickoffStr$viewsStr"

            b.root.setOnClickListener { onMatchClick(match) }

            b.root.setOnKeyListener { _, keyCode, event ->
                if (isTv && event.action == KeyEvent.ACTION_DOWN &&
                    keyCode == KeyEvent.KEYCODE_DPAD_LEFT &&
                    position % spanCount == 0
                ) {
                    onLeftEdgeDpadLeft()
                    true
                } else {
                    false
                }
            }
        }
    }
}
