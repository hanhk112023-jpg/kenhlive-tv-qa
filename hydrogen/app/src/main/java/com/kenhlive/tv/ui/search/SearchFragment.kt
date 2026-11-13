package com.kenhlive.tv.ui.search

import android.os.Bundle
import android.view.KeyEvent
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.view.inputmethod.EditorInfo
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.kenhlive.tv.databinding.FragmentSearchBinding
import com.kenhlive.tv.databinding.ItemScheduleDayHeaderBinding
import com.kenhlive.tv.databinding.ItemScheduleRowBinding
import com.kenhlive.tv.logic.TeamNameMatcher
import com.kenhlive.tv.model.IptvChannel
import com.kenhlive.tv.model.MatchModel
import com.kenhlive.tv.model.MovieItem
import com.kenhlive.tv.repository.MovieRepository
import com.kenhlive.tv.ui.MainActivity
import com.kenhlive.tv.ui.iptv.IptvViewModel
import com.kenhlive.tv.ui.movies.MovieDetailActivity
import com.kenhlive.tv.ui.player.SportsPlayerActivity
import com.kenhlive.tv.ui.player.TvPlayerActivity
import com.kenhlive.tv.ui.sports.SportsViewModel
import com.kenhlive.tv.util.DeviceUtils
import com.kenhlive.tv.util.TvFocusHelper
import kotlinx.coroutines.launch

sealed class SearchResultItem {
    data class GroupHeader(val title: String) : SearchResultItem()
    data class MatchResult(val match: MatchModel) : SearchResultItem()
    data class ChannelResult(val channel: IptvChannel) : SearchResultItem()
    data class MovieResult(val movie: MovieItem) : SearchResultItem()
}

class SearchFragment : Fragment() {

    private var _binding: FragmentSearchBinding? = null
    private val binding get() = _binding!!
    private val sportsVm: SportsViewModel by activityViewModels()
    private val iptvVm: IptvViewModel by activityViewModels()
    private val movieRepo = MovieRepository()
    private lateinit var adapter: SearchAdapter

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentSearchBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        val isTv = DeviceUtils.isTv(requireContext())
        adapter = SearchAdapter(
            isTv = isTv,
            onItemClick = { item ->
                when (item) {
                    is SearchResultItem.MatchResult ->
                        SportsPlayerActivity.start(requireContext(), item.match)
                    is SearchResultItem.ChannelResult ->
                        TvPlayerActivity.start(
                            requireContext(),
                            listOf(item.channel),
                            0,
                            listOf(""),
                            listOf(0)
                        )
                    is SearchResultItem.MovieResult ->
                        MovieDetailActivity.start(requireContext(), item.movie.slug, item.movie.name)
                    else -> {}
                }
            },
            onLeftDpad = { (activity as? MainActivity)?.openTvRail() }
        )
        binding.rvSearchResults.layoutManager = LinearLayoutManager(requireContext())
        binding.rvSearchResults.adapter = adapter

        binding.btnSearchGo.setOnClickListener { runSearch() }
        binding.etSearchQuery.setOnEditorActionListener { _, actionId, _ ->
            if (actionId == EditorInfo.IME_ACTION_SEARCH) {
                runSearch()
                true
            } else false
        }
    }

    private fun runSearch() {
        val rawQuery = binding.etSearchQuery.text?.toString()?.trim().orEmpty()
        if (rawQuery.isEmpty()) return
        val normQuery = TeamNameMatcher.normalize(rawQuery)

        binding.progressSearch.visibility = View.VISIBLE
        viewLifecycleOwner.lifecycleScope.launch {
            val grouped = mutableListOf<SearchResultItem>()

            val matchedMatches = sportsVm.uiState.value.matches.filter {
                TeamNameMatcher.normalize("${it.homeTeam} ${it.awayTeam} ${it.leagueName}")
                    .contains(normQuery)
            }
            if (matchedMatches.isNotEmpty()) {
                grouped.add(SearchResultItem.GroupHeader("Thể thao (${matchedMatches.size})"))
                matchedMatches.forEach { grouped.add(SearchResultItem.MatchResult(it)) }
            }

            val matchedChannels = iptvVm.uiState.value.channels.filter {
                TeamNameMatcher.normalize("${it.name} ${it.groupTitle}").contains(normQuery)
            }
            if (matchedChannels.isNotEmpty()) {
                grouped.add(SearchResultItem.GroupHeader("Truyền hình (${matchedChannels.size})"))
                matchedChannels.forEach { grouped.add(SearchResultItem.ChannelResult(it)) }
            }

            val matchedMovies = runCatching { movieRepo.searchMovies(rawQuery) }.getOrElse { emptyList() }
            if (matchedMovies.isNotEmpty()) {
                grouped.add(SearchResultItem.GroupHeader("Phim truyện (${matchedMovies.size})"))
                matchedMovies.forEach { grouped.add(SearchResultItem.MovieResult(it)) }
            }

            binding.progressSearch.visibility = View.GONE
            adapter.submit(grouped)
        }
    }

    fun focusContent(): Boolean = _binding?.etSearchQuery?.requestFocus() ?: false

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }

    private class SearchAdapter(
        private val isTv: Boolean,
        private val onItemClick: (SearchResultItem) -> Unit,
        private val onLeftDpad: () -> Unit
    ) : RecyclerView.Adapter<RecyclerView.ViewHolder>() {

        private val items = mutableListOf<SearchResultItem>()

        fun submit(list: List<SearchResultItem>) {
            items.clear()
            items.addAll(list)
            notifyDataSetChanged()
        }

        override fun getItemViewType(position: Int): Int =
            if (items[position] is SearchResultItem.GroupHeader) 0 else 1

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
                is SearchResultItem.GroupHeader -> (holder as HeaderVH).bind(item.title)
                else -> (holder as RowVH).bind(item)
            }
        }

        override fun getItemCount(): Int = items.size

        class HeaderVH(private val b: ItemScheduleDayHeaderBinding) : RecyclerView.ViewHolder(b.root) {
            fun bind(title: String) {
                b.tvDayHeader.text = title
            }
        }

        inner class RowVH(private val b: ItemScheduleRowBinding) : RecyclerView.ViewHolder(b.root) {
            init {
                if (isTv) TvFocusHelper.attachFocusScale(b.root)
            }
            fun bind(item: SearchResultItem) {
                when (item) {
                    is SearchResultItem.MatchResult -> {
                        b.tvKickoff.text = item.match.leagueName.take(6)
                        b.tvMatchTitle.text = "${item.match.homeTeam} vs ${item.match.awayTeam}"
                        b.tvScheduleScore.text = item.match.displayScoreOrVs()
                    }
                    is SearchResultItem.ChannelResult -> {
                        b.tvKickoff.text = "TV"
                        b.tvMatchTitle.text = item.channel.name
                        b.tvScheduleScore.text = item.channel.groupTitle.take(8)
                    }
                    is SearchResultItem.MovieResult -> {
                        b.tvKickoff.text = "PHIM"
                        b.tvMatchTitle.text = item.movie.name
                        b.tvScheduleScore.text = if (item.movie.year > 0) "${item.movie.year}" else ""
                    }
                    else -> {}
                }
                b.root.setOnClickListener { onItemClick(item) }
                b.root.setOnKeyListener { _, keyCode, event ->
                    if (isTv && event.action == KeyEvent.ACTION_DOWN && keyCode == KeyEvent.KEYCODE_DPAD_LEFT) {
                        onLeftDpad()
                        true
                    } else false
                }
            }
        }
    }
}
