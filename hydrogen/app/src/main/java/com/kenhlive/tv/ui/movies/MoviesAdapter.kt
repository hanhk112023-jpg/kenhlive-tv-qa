package com.kenhlive.tv.ui.movies

import android.view.KeyEvent
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import coil.load
import coil.size.Precision
import com.kenhlive.tv.databinding.ItemMovieCardBinding
import com.kenhlive.tv.model.MovieItem
import com.kenhlive.tv.util.TvFocusHelper

class MoviesAdapter(
    private val isTv: Boolean,
    private val spanCount: Int,
    private val onMovieClick: (MovieItem) -> Unit,
    private val onLeftEdgeDpadLeft: () -> Unit
) : ListAdapter<MovieItem, MoviesAdapter.MovieVH>(MovieDiffCallback) {

    object MovieDiffCallback : DiffUtil.ItemCallback<MovieItem>() {
        override fun areItemsTheSame(oldItem: MovieItem, newItem: MovieItem): Boolean =
            oldItem.slug == newItem.slug

        override fun areContentsTheSame(oldItem: MovieItem, newItem: MovieItem): Boolean =
            oldItem == newItem
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): MovieVH {
        val b = ItemMovieCardBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return MovieVH(b)
    }

    override fun onBindViewHolder(holder: MovieVH, position: Int) {
        holder.bind(getItem(position), position)
    }

    inner class MovieVH(private val b: ItemMovieCardBinding) : RecyclerView.ViewHolder(b.root) {
        init {
            if (isTv) TvFocusHelper.attachFocusScale(b.root)
        }

        fun bind(movie: MovieItem, position: Int) {
            b.tvMovieTitle.text = movie.name
            val yearStr = if (movie.year > 0) "${movie.year}" else ""
            val langStr = if (movie.lang.isNotBlank()) " · ${movie.lang}" else ""
            b.tvMovieMeta.text = "$yearStr$langStr".trimStart(' ', '·')

            val badgeText = movie.episodeCurrent.ifBlank { movie.quality }
            if (badgeText.isNotBlank()) {
                b.tvMovieBadge.text = badgeText
                b.tvMovieBadge.visibility = View.VISIBLE
            } else {
                b.tvMovieBadge.visibility = View.GONE
            }

            b.ivPoster.load(movie.posterUrl.ifBlank { movie.thumbUrl }) {
                size(300, 420)
                precision(Precision.INEXACT)
                crossfade(true)
            }

            b.root.setOnClickListener { onMovieClick(movie) }
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
