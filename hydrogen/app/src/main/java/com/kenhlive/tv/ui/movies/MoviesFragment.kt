package com.kenhlive.tv.ui.movies

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.recyclerview.widget.GridLayoutManager
import com.kenhlive.tv.databinding.FragmentMoviesBinding
import com.kenhlive.tv.ui.MainActivity
import com.kenhlive.tv.util.DeviceUtils
import kotlinx.coroutines.launch

class MoviesFragment : Fragment() {

    private var _binding: FragmentMoviesBinding? = null
    private val binding get() = _binding!!
    private val viewModel: MoviesViewModel by activityViewModels()
    private lateinit var adapter: MoviesAdapter

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentMoviesBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        val isTv = DeviceUtils.isTv(requireContext())
        val spanCount = if (isTv) 5 else 2

        adapter = MoviesAdapter(
            isTv = isTv,
            spanCount = spanCount,
            onMovieClick = { movie -> MovieDetailActivity.start(requireContext(), movie.slug, movie.name) },
            onLeftEdgeDpadLeft = { (activity as? MainActivity)?.openTvRail() }
        )

        binding.rvMovies.layoutManager = GridLayoutManager(requireContext(), spanCount)
        binding.rvMovies.adapter = adapter

        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.uiState.collect { state ->
                    binding.progressMovies.visibility = if (state.isLoading) View.VISIBLE else View.GONE
                    binding.tvMoviesEmpty.visibility =
                        if (!state.isLoading && state.movies.isEmpty()) View.VISIBLE else View.GONE
                    adapter.submitList(state.movies)
                }
            }
        }
    }

    fun focusContent(): Boolean = _binding?.rvMovies?.requestFocus() ?: false

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
