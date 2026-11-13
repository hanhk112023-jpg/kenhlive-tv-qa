package com.kenhlive.tv.ui.iptv

import android.os.Bundle
import android.view.KeyEvent
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.recyclerview.widget.GridLayoutManager
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.kenhlive.tv.databinding.FragmentIptvBinding
import com.kenhlive.tv.databinding.ItemFilterChipBinding
import com.kenhlive.tv.model.EpgProgram
import com.kenhlive.tv.model.IptvChannel
import com.kenhlive.tv.ui.MainActivity
import com.kenhlive.tv.ui.player.TvPlayerActivity
import com.kenhlive.tv.util.DeviceUtils
import kotlinx.coroutines.launch

class IptvFragment : Fragment() {

    private var _binding: FragmentIptvBinding? = null
    private val binding get() = _binding!!
    private val viewModel: IptvViewModel by activityViewModels()
    private lateinit var adapter: IptvAdapter
    private lateinit var groupAdapter: GroupChipAdapter

    private var allChannels: List<IptvChannel> = emptyList()
    private var filteredChannels: List<IptvChannel> = emptyList()
    private var epgMap: Map<String, EpgProgram> = emptyMap()
    private var selectedGroup: String = "Tất cả"

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentIptvBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        val isTv = DeviceUtils.isTv(requireContext())
        val spanCount = if (isTv) 2 else 1

        groupAdapter = GroupChipAdapter(
            isTv = isTv,
            onSelect = { group ->
                selectedGroup = group
                applyGroupFilter(isLoading = false)
            },
            onLeftEdgeDpadLeft = { (activity as? MainActivity)?.openTvRail() }
        )
        binding.rvIptvGroups.apply {
            layoutManager = LinearLayoutManager(requireContext(), LinearLayoutManager.HORIZONTAL, false)
            adapter = groupAdapter
        }

        adapter = IptvAdapter(
            isTv = isTv,
            spanCount = spanCount,
            onChannelClick = { ch ->
                val list = filteredChannels.ifEmpty { listOf(ch) }
                val idx = list.indexOfFirst { it.id == ch.id }.coerceAtLeast(0)
                val now = System.currentTimeMillis()
                val epgTitles = list.map { c ->
                    epgMap[c.tvgId]?.title ?: epgMap[c.name]?.title ?: ""
                }
                val epgProgress = list.map { c ->
                    val epg = epgMap[c.tvgId] ?: epgMap[c.name]
                    if (epg != null && epg.endEpochMs > epg.startEpochMs) {
                        val dur = epg.endEpochMs - epg.startEpochMs
                        val elapsed = (now - epg.startEpochMs).coerceIn(0L, dur)
                        ((elapsed * 100L) / dur).toInt()
                    } else 0
                }
                TvPlayerActivity.start(requireContext(), list, idx, epgTitles, epgProgress)
            },
            onLeftEdgeDpadLeft = { (activity as? MainActivity)?.openTvRail() }
        )

        binding.rvIptv.apply {
            layoutManager = if (isTv) {
                GridLayoutManager(requireContext(), spanCount)
            } else {
                LinearLayoutManager(requireContext())
            }
            setHasFixedSize(true)
            setItemViewCacheSize(24)
            adapter = this@IptvFragment.adapter
        }

        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.uiState.collect { state ->
                    binding.progressIptv.visibility = if (state.isLoading) View.VISIBLE else View.GONE
                    allChannels = state.channels
                    epgMap = state.epgMap

                    val groups = listOf("Tất cả") + state.channels
                        .map { it.groupTitle }
                        .filter { it.isNotBlank() }
                        .distinct()
                        .take(12)
                    groupAdapter.submit(groups, selectedGroup)
                    applyGroupFilter(state.isLoading)
                }
            }
        }
    }

    private fun applyGroupFilter(isLoading: Boolean) {
        filteredChannels = if (selectedGroup == "Tất cả") {
            allChannels
        } else {
            allChannels.filter { it.groupTitle == selectedGroup }
        }
        binding.tvIptvCount.text = "${filteredChannels.size} kênh"
        binding.tvIptvEmpty.visibility =
            if (!isLoading && filteredChannels.isEmpty()) View.VISIBLE else View.GONE
        adapter.submitData(filteredChannels, epgMap)
    }

    fun focusContent(): Boolean = _binding?.rvIptv?.requestFocus() ?: false

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }

    private class GroupChipAdapter(
        private val isTv: Boolean,
        private val onSelect: (String) -> Unit,
        private val onLeftEdgeDpadLeft: () -> Unit
    ) : RecyclerView.Adapter<GroupChipAdapter.ChipVH>() {

        private val groups = mutableListOf<String>()
        private var current = "Tất cả"

        fun submit(list: List<String>, selected: String) {
            groups.clear()
            groups.addAll(list)
            current = selected
            notifyDataSetChanged()
        }

        override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ChipVH {
            val b = ItemFilterChipBinding.inflate(LayoutInflater.from(parent.context), parent, false)
            return ChipVH(b)
        }

        override fun onBindViewHolder(holder: ChipVH, position: Int) {
            holder.bind(groups[position], position)
        }

        override fun getItemCount(): Int = groups.size

        inner class ChipVH(private val b: ItemFilterChipBinding) : RecyclerView.ViewHolder(b.root) {
            fun bind(name: String, position: Int) {
                b.tvFilterChip.text = name
                b.tvFilterChip.isSelected = (name == current)
                b.tvFilterChip.setOnClickListener {
                    current = name
                    notifyDataSetChanged()
                    onSelect(name)
                }
                b.tvFilterChip.setOnKeyListener { _, keyCode, event ->
                    if (isTv && position == 0 && event.action == KeyEvent.ACTION_DOWN &&
                        keyCode == KeyEvent.KEYCODE_DPAD_LEFT
                    ) {
                        onLeftEdgeDpadLeft()
                        true
                    } else false
                }
            }
        }
    }
}
