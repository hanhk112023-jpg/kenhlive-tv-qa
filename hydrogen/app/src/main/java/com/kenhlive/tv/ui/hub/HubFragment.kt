package com.kenhlive.tv.ui.hub

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.recyclerview.widget.LinearLayoutManager
import com.kenhlive.tv.databinding.FragmentHubBinding
import com.kenhlive.tv.model.MatchState
import com.kenhlive.tv.ui.MainActivity
import com.kenhlive.tv.ui.iptv.IptvViewModel
import com.kenhlive.tv.ui.movies.MoviesViewModel
import com.kenhlive.tv.ui.player.SportsPlayerActivity
import com.kenhlive.tv.ui.sports.MatchCardAdapter
import com.kenhlive.tv.ui.sports.SportsViewModel
import com.kenhlive.tv.util.DeviceUtils
import com.kenhlive.tv.util.TvFocusHelper
import kotlinx.coroutines.launch

class HubFragment : Fragment() {

    private var _binding: FragmentHubBinding? = null
    private val binding get() = _binding!!
    private val sportsVm: SportsViewModel by activityViewModels()
    private val iptvVm: IptvViewModel by activityViewModels()
    private val moviesVm: MoviesViewModel by activityViewModels()
    private lateinit var liveAdapter: MatchCardAdapter

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentHubBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        val isTv = DeviceUtils.isTv(requireContext())

        if (isTv) {
            listOf(
                binding.cardHubSports,
                binding.cardHubIptv,
                binding.cardHubMovies,
                binding.btnHubSettings,
                binding.btnHubReport
            ).forEach { TvFocusHelper.attachFocusScale(it) }
        }

        binding.cardHubSports.setOnClickListener {
            (activity as? MainActivity)?.selectTab(MainActivity.TAB_SPORTS, hideRailAfter = true)
        }
        binding.cardHubIptv.setOnClickListener {
            (activity as? MainActivity)?.selectTab(MainActivity.TAB_IPTV, hideRailAfter = true)
        }
        binding.cardHubMovies.setOnClickListener {
            (activity as? MainActivity)?.selectTab(MainActivity.TAB_MOVIES, hideRailAfter = true)
        }
        binding.btnHubSettings.setOnClickListener {
            (activity as? MainActivity)?.selectTab(MainActivity.TAB_SETTINGS, hideRailAfter = true)
        }
        binding.btnHubReport.setOnClickListener {
            runCatching {
                startActivity(Intent(Intent.ACTION_VIEW, Uri.parse("https://t.me/kenhlivetv")))
            }
        }

        liveAdapter = MatchCardAdapter(
            isTv = isTv,
            spanCount = 1,
            onMatchClick = { match -> SportsPlayerActivity.start(requireContext(), match) },
            onLeftEdgeDpadLeft = { (activity as? MainActivity)?.openTvRail() }
        )
        binding.rvHubLive.layoutManager =
            LinearLayoutManager(requireContext(), LinearLayoutManager.HORIZONTAL, false)
        binding.rvHubLive.adapter = liveAdapter

        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                launch {
                    sportsVm.uiState.collect { state ->
                        val realLive = state.matches.filter { it.state == MatchState.LIVE }
                        binding.tvHubSportsCount.text = "${realLive.size} live"
                        liveAdapter.submitList(realLive)
                    }
                }
                launch {
                    iptvVm.uiState.collect { state ->
                        binding.tvHubIptvCount.text = "${state.channels.size} kênh"
                    }
                }
                launch {
                    moviesVm.uiState.collect { state ->
                        binding.tvHubMoviesCount.text = "${state.movies.size} phim"
                    }
                }
            }
        }
    }

    fun focusContent(): Boolean = _binding?.cardHubSports?.requestFocus() ?: false

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
