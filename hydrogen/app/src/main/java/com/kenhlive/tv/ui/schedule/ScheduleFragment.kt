package com.kenhlive.tv.ui.schedule

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
import com.kenhlive.tv.databinding.FragmentScheduleBinding
import com.kenhlive.tv.ui.MainActivity
import com.kenhlive.tv.ui.player.SportsPlayerActivity
import com.kenhlive.tv.ui.sports.SportsViewModel
import com.kenhlive.tv.util.DeviceUtils
import kotlinx.coroutines.launch

class ScheduleFragment : Fragment() {

    private var _binding: FragmentScheduleBinding? = null
    private val binding get() = _binding!!
    private val viewModel: SportsViewModel by activityViewModels()
    private lateinit var adapter: ScheduleAdapter

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentScheduleBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        val isTv = DeviceUtils.isTv(requireContext())
        adapter = ScheduleAdapter(
            isTv = isTv,
            onMatchClick = { match -> SportsPlayerActivity.start(requireContext(), match) },
            onLeftDpad = { (activity as? MainActivity)?.openTvRail() }
        )
        binding.rvSchedule.layoutManager = LinearLayoutManager(requireContext())
        binding.rvSchedule.adapter = adapter

        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.uiState.collect { state ->
                    binding.progressSchedule.visibility = if (state.isLoading) View.VISIBLE else View.GONE
                    adapter.submitMatches(state.matches)
                    val empty = !state.isLoading && adapter.itemCount == 0
                    binding.tvScheduleEmpty.visibility = if (empty) View.VISIBLE else View.GONE
                }
            }
        }
    }

    fun focusContent(): Boolean = _binding?.rvSchedule?.requestFocus() ?: false

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
