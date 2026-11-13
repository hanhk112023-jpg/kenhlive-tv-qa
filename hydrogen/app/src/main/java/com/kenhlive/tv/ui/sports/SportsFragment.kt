package com.kenhlive.tv.ui.sports

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
import coil.load
import coil.size.Precision
import com.kenhlive.tv.R
import com.kenhlive.tv.databinding.FragmentSportsBinding
import com.kenhlive.tv.logic.TimeUtils
import com.kenhlive.tv.model.MatchModel
import com.kenhlive.tv.model.MatchState
import com.kenhlive.tv.ui.MainActivity
import com.kenhlive.tv.ui.player.SportsPlayerActivity
import com.kenhlive.tv.util.DeviceUtils
import com.kenhlive.tv.util.TvFocusHelper
import kotlinx.coroutines.launch

class SportsFragment : Fragment() {

    private enum class SportsFilter { ALL, LIVE, UPCOMING }

    private var _binding: FragmentSportsBinding? = null
    private val binding get() = _binding!!
    private val viewModel: SportsViewModel by activityViewModels()
    private lateinit var adapter: MatchCardAdapter
    private var currentFilter = SportsFilter.ALL
    private var latestMatches: List<MatchModel> = emptyList()

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentSportsBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        val isTv = DeviceUtils.isTv(requireContext())
        val spanCount = if (isTv) 2 else 1

        adapter = MatchCardAdapter(
            isTv = isTv,
            spanCount = spanCount,
            onMatchClick = { match -> SportsPlayerActivity.start(requireContext(), match) },
            onLeftEdgeDpadLeft = { (activity as? MainActivity)?.openTvRail() }
        )

        binding.rvMatches.apply {
            layoutManager = if (isTv) {
                GridLayoutManager(requireContext(), spanCount)
            } else {
                LinearLayoutManager(requireContext())
            }
            setHasFixedSize(true)
            setItemViewCacheSize(20)
            adapter = this@SportsFragment.adapter
        }

        if (isTv) {
            TvFocusHelper.attachFocusScale(binding.heroContainer)
            binding.heroContainer.setOnKeyListener { _, keyCode, event ->
                if (event.action == KeyEvent.ACTION_DOWN && keyCode == KeyEvent.KEYCODE_DPAD_LEFT) {
                    (activity as? MainActivity)?.openTvRail()
                    true
                } else false
            }
            binding.chipFilterAll.setOnKeyListener { _, keyCode, event ->
                if (event.action == KeyEvent.ACTION_DOWN && keyCode == KeyEvent.KEYCODE_DPAD_LEFT) {
                    (activity as? MainActivity)?.openTvRail()
                    true
                } else false
            }
        }

        setupFilterChips()

        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.uiState.collect { state ->
                    binding.progressSports.visibility = if (state.isLoading) View.VISIBLE else View.GONE
                    latestMatches = state.matches
                    binding.heroContainer.visibility = if (state.heroMatch != null) View.VISIBLE else View.GONE

                    state.heroMatch?.let { hero ->
                        binding.tvHeroLeague.text = hero.leagueName
                        binding.tvHeroTitle.text = "${hero.homeTeam} vs ${hero.awayTeam}"
                        binding.tvHeroScore.text = hero.displayScoreOrVs()
                        binding.ivHeroHomeLogo.load(hero.homeLogo) { size(96, 96); precision(Precision.INEXACT) }
                        binding.ivHeroAwayLogo.load(hero.awayLogo) { size(96, 96); precision(Precision.INEXACT) }
                        binding.tvHeroBadge.text = when (hero.state) {
                            MatchState.LIVE -> getString(R.string.kl3_badge_live)
                            MatchState.UPCOMING -> getString(R.string.kl3_badge_upcoming)
                            MatchState.FINISHED -> getString(R.string.kl3_badge_finished)
                        }
                        binding.tvHeroBadge.setBackgroundResource(
                            when (hero.state) {
                                MatchState.LIVE -> R.drawable.kl3_badge_live
                                MatchState.UPCOMING -> R.drawable.kl3_badge_upcoming
                                MatchState.FINISHED -> R.drawable.kl3_badge_finished
                            }
                        )
                        val timeStr = TimeUtils.formatKickoffShortDateTime(hero.kickoffEpochMs)
                        val blv = if (hero.commentator.isNotBlank()) "${hero.commentator} · " else ""
                        binding.tvHeroMeta.text = "$blv$timeStr"
                        binding.heroContainer.setOnClickListener {
                            SportsPlayerActivity.start(requireContext(), hero)
                        }
                    }

                    applyFilter(state.isLoading)
                }
            }
        }
    }

    private fun setupFilterChips() {
        val chips = listOf(
            binding.chipFilterAll to SportsFilter.ALL,
            binding.chipFilterLive to SportsFilter.LIVE,
            binding.chipFilterUpcoming to SportsFilter.UPCOMING
        )
        chips.forEach { (chip, filter) ->
            chip.isSelected = (filter == currentFilter)
            chip.setOnClickListener {
                currentFilter = filter
                chips.forEach { (c, f) -> c.isSelected = (f == currentFilter) }
                applyFilter(isLoading = false)
            }
        }
    }

    private fun applyFilter(isLoading: Boolean) {
        val filtered = when (currentFilter) {
            SportsFilter.ALL -> latestMatches
            SportsFilter.LIVE -> latestMatches.filter { it.state == MatchState.LIVE }
            SportsFilter.UPCOMING -> latestMatches.filter { it.state == MatchState.UPCOMING }
        }
        adapter.submitList(filtered)
        binding.tvSportsEmpty.visibility =
            if (!isLoading && filtered.isEmpty()) View.VISIBLE else View.GONE
    }

    fun focusContent(): Boolean {
        return if (_binding != null && binding.heroContainer.visibility == View.VISIBLE) {
            binding.heroContainer.requestFocus()
        } else {
            _binding?.rvMatches?.requestFocus() ?: false
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
