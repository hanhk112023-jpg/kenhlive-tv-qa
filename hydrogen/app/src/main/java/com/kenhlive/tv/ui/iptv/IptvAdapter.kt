package com.kenhlive.tv.ui.iptv

import android.view.KeyEvent
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import coil.load
import coil.size.Precision
import com.kenhlive.tv.databinding.ItemIptvChannelBinding
import com.kenhlive.tv.model.EpgProgram
import com.kenhlive.tv.model.IptvChannel
import com.kenhlive.tv.util.TvFocusHelper

class IptvAdapter(
    private val isTv: Boolean,
    private val spanCount: Int,
    private val onChannelClick: (IptvChannel) -> Unit,
    private val onLeftEdgeDpadLeft: () -> Unit
) : ListAdapter<IptvChannel, IptvAdapter.ChannelVH>(ChannelDiffCallback) {

    object ChannelDiffCallback : DiffUtil.ItemCallback<IptvChannel>() {
        override fun areItemsTheSame(oldItem: IptvChannel, newItem: IptvChannel): Boolean =
            oldItem.id == newItem.id

        override fun areContentsTheSame(oldItem: IptvChannel, newItem: IptvChannel): Boolean =
            oldItem == newItem
    }

    private var epgMap: Map<String, EpgProgram> = emptyMap()

    fun submitData(channels: List<IptvChannel>, epg: Map<String, EpgProgram>) {
        epgMap = epg
        submitList(channels)
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ChannelVH {
        val b = ItemIptvChannelBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return ChannelVH(b)
    }

    override fun onBindViewHolder(holder: ChannelVH, position: Int) {
        holder.bind(getItem(position), position)
    }

    inner class ChannelVH(private val b: ItemIptvChannelBinding) : RecyclerView.ViewHolder(b.root) {
        init {
            if (isTv) TvFocusHelper.attachFocusScale(b.root)
        }

        fun bind(ch: IptvChannel, position: Int) {
            b.tvChannelName.text = ch.name
            b.tvChannelGroup.text = ch.groupTitle

            val epg = epgMap[ch.tvgId] ?: epgMap[ch.name]
            if (epg != null && epg.title.isNotBlank()) {
                b.tvChannelEpg.text = "Đang chiếu: ${epg.title}"
                val duration = epg.endEpochMs - epg.startEpochMs
                if (duration > 0L) {
                    val elapsed = (System.currentTimeMillis() - epg.startEpochMs).coerceIn(0L, duration)
                    b.progressEpg.progress = ((elapsed * 100L) / duration).toInt()
                    b.progressEpg.visibility = View.VISIBLE
                } else {
                    b.progressEpg.visibility = View.GONE
                }
            } else {
                b.tvChannelEpg.text = "Phát trực tiếp 24/7"
                b.progressEpg.visibility = View.GONE
            }

            b.ivChannelLogo.load(ch.logoUrl) {
                size(112, 88)
                precision(Precision.INEXACT)
                crossfade(true)
            }

            b.root.setOnClickListener { onChannelClick(ch) }
            b.root.setOnKeyListener { _, keyCode, event ->
                if (isTv && event.action == KeyEvent.ACTION_DOWN &&
                    keyCode == KeyEvent.KEYCODE_DPAD_LEFT &&
                    position % spanCount == 0
                ) {
                    onLeftEdgeDpadLeft()
                    true
                } else false
            }
        }
    }
}
