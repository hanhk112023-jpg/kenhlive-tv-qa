package com.kenhlive.tv.ui.movies

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.GridLayoutManager
import androidx.recyclerview.widget.RecyclerView
import coil.load
import com.kenhlive.tv.databinding.ActivityMovieDetailBinding
import com.kenhlive.tv.databinding.ItemEpisodeChipBinding
import com.kenhlive.tv.model.MovieEpisode
import com.kenhlive.tv.repository.MovieRepository
import com.kenhlive.tv.ui.player.MoviePlayerActivity
import com.kenhlive.tv.util.DeviceUtils
import com.kenhlive.tv.util.TvFocusHelper
import kotlinx.coroutines.launch

class MovieDetailActivity : AppCompatActivity() {

    companion object {
        private const val EXTRA_SLUG = "extra_slug"
        private const val EXTRA_TITLE = "extra_title"

        fun start(context: Context, slug: String, title: String) {
            val intent = Intent(context, MovieDetailActivity::class.java).apply {
                putExtra(EXTRA_SLUG, slug)
                putExtra(EXTRA_TITLE, title)
            }
            context.startActivity(intent)
        }
    }

    private lateinit var binding: ActivityMovieDetailBinding
    private val repository = MovieRepository()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMovieDetailBinding.inflate(layoutInflater)
        setContentView(binding.root)

        val slug = intent.getStringExtra(EXTRA_SLUG) ?: ""
        val fallbackTitle = intent.getStringExtra(EXTRA_TITLE) ?: ""
        binding.tvDetailTitle.text = fallbackTitle

        val isTv = DeviceUtils.isTv(this)
        val spanCount = if (isTv) 6 else 3
        binding.rvEpisodes.layoutManager = GridLayoutManager(this, spanCount)

        binding.progressDetail.visibility = View.VISIBLE
        lifecycleScope.launch {
            val detail = runCatching { repository.fetchMovieDetail(slug) }.getOrNull()
            binding.progressDetail.visibility = View.GONE
            if (detail != null) {
                binding.tvDetailTitle.text = detail.name
                val cats = detail.categories.joinToString(", ")
                binding.tvDetailSub.text = "${detail.year} · ${detail.quality} · ${detail.lang} · $cats"
                binding.tvDetailDesc.text = detail.content
                binding.ivDetailPoster.load(detail.posterUrl.ifBlank { detail.thumbUrl }) { crossfade(true) }

                val allEpisodes = detail.servers.firstOrNull()?.episodes ?: emptyList()
                binding.rvEpisodes.adapter = EpisodeAdapter(isTv, allEpisodes) { index ->
                    MoviePlayerActivity.start(
                        context = this@MovieDetailActivity,
                        movieName = detail.name,
                        episodes = allEpisodes,
                        selectedIndex = index
                    )
                }
            } else {
                binding.tvDetailDesc.text = "Không tải được chi tiết phim."
            }
        }
    }

    private class EpisodeAdapter(
        private val isTv: Boolean,
        private val episodes: List<MovieEpisode>,
        private val onClick: (Int) -> Unit
    ) : RecyclerView.Adapter<EpisodeAdapter.EpVH>() {

        override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): EpVH {
            val b = ItemEpisodeChipBinding.inflate(LayoutInflater.from(parent.context), parent, false)
            return EpVH(b)
        }

        override fun onBindViewHolder(holder: EpVH, position: Int) = holder.bind(episodes[position], position)
        override fun getItemCount(): Int = episodes.size

        inner class EpVH(private val b: ItemEpisodeChipBinding) : RecyclerView.ViewHolder(b.root) {
            init {
                if (isTv) TvFocusHelper.attachFocusScale(b.root)
            }
            fun bind(ep: MovieEpisode, position: Int) {
                b.tvEpisodeName.text = ep.name
                b.root.setOnClickListener { onClick(position) }
            }
        }
    }
}
