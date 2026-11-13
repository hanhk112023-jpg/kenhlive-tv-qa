package com.kenhlive.tv.ui.player

import android.annotation.SuppressLint
import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.view.View
import android.view.ViewGroup
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Button
import android.widget.SeekBar
import android.widget.TextView
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.media3.common.MediaItem
import androidx.media3.common.PlaybackException
import androidx.media3.common.Player
import androidx.media3.datasource.DefaultHttpDataSource
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.exoplayer.hls.HlsMediaSource
import androidx.media3.ui.AspectRatioFrameLayout
import androidx.media3.ui.PlayerView
import com.kenhlive.tv.R
import com.kenhlive.tv.model.MovieEpisode
import com.kenhlive.tv.util.DeviceUtils
import com.kenhlive.tv.util.TvFocusHelper

class MoviePlayerActivity : AppCompatActivity() {

    companion object {
        private const val EXTRA_MOVIE_NAME = "extra_movie_name"
        private const val EXTRA_EP_INDEX = "extra_ep_index"
        private const val EXTRA_EP_NAMES = "extra_ep_names"
        private const val EXTRA_EP_M3U8 = "extra_ep_m3u8"
        private const val EXTRA_EP_EMBED = "extra_ep_embed"

        fun start(context: Context, movieName: String, episodes: List<MovieEpisode>, selectedIndex: Int) {
            val intent = Intent(context, MoviePlayerActivity::class.java).apply {
                putExtra(EXTRA_MOVIE_NAME, movieName)
                putExtra(EXTRA_EP_INDEX, selectedIndex)
                putStringArrayListExtra(EXTRA_EP_NAMES, ArrayList(episodes.map { it.name }))
                putStringArrayListExtra(EXTRA_EP_M3U8, ArrayList(episodes.map { it.linkM3u8 }))
                putStringArrayListExtra(EXTRA_EP_EMBED, ArrayList(episodes.map { it.linkEmbed }))
            }
            context.startActivity(intent)
        }
    }

    private var player: ExoPlayer? = null
    private lateinit var playerView: PlayerView
    private var embedWebView: WebView? = null
    private lateinit var tvTitle: TextView
    private lateinit var tvTimeCurrent: TextView
    private lateinit var tvTimeTotal: TextView
    private lateinit var seekBar: SeekBar
    private lateinit var btnPlayPause: Button
    private lateinit var btnNextEp: Button
    private lateinit var tvError: TextView

    private var movieName = ""
    private var epNames: List<String> = emptyList()
    private var epM3u8: List<String> = emptyList()
    private var epEmbed: List<String> = emptyList()
    private var currentEp = 0
    private var playbackSpeed = 1.0f

    private val handler = Handler(Looper.getMainLooper())
    private val progressTicker = object : Runnable {
        override fun run() {
            val p = player
            if (p != null && p.duration > 0) {
                val pos = p.currentPosition.coerceAtLeast(0L)
                val dur = p.duration.coerceAtLeast(1L)
                seekBar.max = 1000
                seekBar.progress = ((pos * 1000L) / dur).toInt()
                tvTimeCurrent.text = formatDuration(pos)
                tvTimeTotal.text = formatDuration(dur)
            }
            handler.postDelayed(this, 1000L)
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_player_movie)

        playerView = findViewById(R.id.playerView)
        tvTitle = findViewById(R.id.tvMoviePlayerTitle)
        tvTimeCurrent = findViewById(R.id.tvMovieTimeCurrent)
        tvTimeTotal = findViewById(R.id.tvMovieTimeTotal)
        seekBar = findViewById(R.id.seekMovie)
        btnPlayPause = findViewById(R.id.btnMoviePlayPause)
        btnNextEp = findViewById(R.id.btnMovieNextEp)
        tvError = findViewById(R.id.tvPlayerError)

        val btnRewind = findViewById<Button>(R.id.btnMovieRewind)
        val btnForward = findViewById<Button>(R.id.btnMovieForward)
        val btnEpisodes = findViewById<Button>(R.id.btnMovieEpisodes)
        val btnOptions = findViewById<Button>(R.id.btnMovieOptions)

        movieName = intent.getStringExtra(EXTRA_MOVIE_NAME) ?: ""
        epNames = intent.getStringArrayListExtra(EXTRA_EP_NAMES) ?: emptyList()
        epM3u8 = intent.getStringArrayListExtra(EXTRA_EP_M3U8) ?: emptyList()
        epEmbed = intent.getStringArrayListExtra(EXTRA_EP_EMBED) ?: emptyList()
        currentEp = intent.getIntExtra(EXTRA_EP_INDEX, 0).coerceIn(0, (epNames.size - 1).coerceAtLeast(0))

        if (DeviceUtils.isTv(this)) {
            listOf(btnRewind, btnPlayPause, btnForward, btnNextEp, btnEpisodes, btnOptions)
                .forEach { TvFocusHelper.attachFocusScale(it) }
            btnPlayPause.requestFocus()
        }

        btnRewind.setOnClickListener { player?.let { it.seekTo((it.currentPosition - 10_000L).coerceAtLeast(0L)) } }
        btnForward.setOnClickListener { player?.let { it.seekTo(it.currentPosition + 10_000L) } }
        btnPlayPause.setOnClickListener {
            val p = player ?: return@setOnClickListener
            if (p.isPlaying) {
                p.pause()
                btnPlayPause.text = "PHÁT"
            } else {
                p.play()
                btnPlayPause.text = "TẠM DỪNG"
            }
        }
        btnNextEp.setOnClickListener {
            if (currentEp + 1 < epNames.size) playEpisode(currentEp + 1)
        }
        btnEpisodes.setOnClickListener { showEpisodePicker() }
        btnOptions.setOnClickListener { showOptions() }

        seekBar.setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
            override fun onProgressChanged(sb: SeekBar?, progress: Int, fromUser: Boolean) {
                if (fromUser) {
                    val dur = player?.duration ?: 0L
                    if (dur > 0) player?.seekTo((dur * progress) / 1000L)
                }
            }
            override fun onStartTrackingTouch(sb: SeekBar?) {}
            override fun onStopTrackingTouch(sb: SeekBar?) {}
        })

        initPlayer()
        if (epNames.isNotEmpty()) {
            playEpisode(currentEp)
        } else {
            showError("Phim này chưa có tập phát.")
        }
    }

    private fun initPlayer() {
        player = ExoPlayerFactory.create(this).also { exo ->
            playerView.player = exo
            exo.addListener(object : Player.Listener {
                override fun onPlayerError(error: PlaybackException) {
                    val fallbackEmbed = epEmbed.getOrNull(currentEp).orEmpty()
                    if (fallbackEmbed.isNotBlank()) {
                        openEmbedFallback(fallbackEmbed)
                    } else {
                        showError("Không thể phát tập phim (${error.errorCodeName}).")
                    }
                }
            })
        }
    }

    private fun playEpisode(index: Int) {
        currentEp = index
        tvError.visibility = View.GONE
        val epTitle = epNames.getOrNull(index) ?: "Tập ${index + 1}"
        tvTitle.text = "$movieName · $epTitle"
        btnNextEp.visibility = if (index + 1 < epNames.size) View.VISIBLE else View.GONE

        val m3u8 = epM3u8.getOrNull(index).orEmpty()
        val embed = epEmbed.getOrNull(index).orEmpty()

        if (m3u8.isBlank() && embed.isNotBlank()) {
            openEmbedFallback(embed)
            return
        }

        playerView.visibility = View.VISIBLE
        embedWebView?.visibility = View.GONE

        val exo = player ?: return
        val factory = DefaultHttpDataSource.Factory()
            .setUserAgent("KenhLive/0.1.12 (Android)")
            .setAllowCrossProtocolRedirects(true)

        exo.setMediaSource(HlsMediaSource.Factory(factory).createMediaSource(MediaItem.fromUri(m3u8)))
        exo.setPlaybackSpeed(playbackSpeed)
        exo.prepare()
        exo.playWhenReady = true
    }

    @SuppressLint("SetJavaScriptEnabled")
    private fun openEmbedFallback(embedUrl: String) {
        player?.stop()
        playerView.visibility = View.GONE
        if (embedWebView == null) {
            embedWebView = WebView(this).apply {
                settings.javaScriptEnabled = true
                settings.mediaPlaybackRequiresUserGesture = false
                webViewClient = WebViewClient()
            }
            (playerView.parent as? ViewGroup)?.addView(embedWebView, 0)
        }
        embedWebView?.visibility = View.VISIBLE
        embedWebView?.loadUrl(embedUrl)
    }

    private fun showEpisodePicker() {
        AlertDialog.Builder(this)
            .setTitle("Chọn tập phim")
            .setSingleChoiceItems(epNames.toTypedArray(), currentEp) { d, idx ->
                playEpisode(idx)
                d.dismiss()
            }
            .show()
    }

    private fun showOptions() {
        val opts = arrayOf(
            "Tốc độ phát (1.0x / 1.25x / 1.5x)",
            "Tỉ lệ khung hình (Vừa / Đầy)",
            "Chuyển sang trình phát Web Embed"
        )
        AlertDialog.Builder(this)
            .setTitle(R.string.kl3_player_options)
            .setItems(opts) { _, which ->
                when (which) {
                    0 -> {
                        playbackSpeed = when (playbackSpeed) {
                            1.0f -> 1.25f
                            1.25f -> 1.5f
                            else -> 1.0f
                        }
                        player?.setPlaybackSpeed(playbackSpeed)
                    }
                    1 -> playerView.resizeMode =
                        if (playerView.resizeMode == AspectRatioFrameLayout.RESIZE_MODE_FIT)
                            AspectRatioFrameLayout.RESIZE_MODE_ZOOM else AspectRatioFrameLayout.RESIZE_MODE_FIT
                    2 -> epEmbed.getOrNull(currentEp)?.takeIf { it.isNotBlank() }?.let { openEmbedFallback(it) }
                }
            }
            .show()
    }

    private fun showError(msg: String) {
        tvError.text = msg
        tvError.visibility = View.VISIBLE
    }

    private fun formatDuration(ms: Long): String {
        val totalSec = ms / 1000L
        val h = totalSec / 3600L
        val m = (totalSec % 3600L) / 60L
        val s = totalSec % 60L
        return if (h > 0) String.format("%d:%02d:%02d", h, m, s) else String.format("%02d:%02d", m, s)
    }

    override fun onStart() {
        super.onStart()
        handler.post(progressTicker)
    }

    override fun onStop() {
        super.onStop()
        handler.removeCallbacks(progressTicker)
        player?.pause()
    }

    override fun onDestroy() {
        super.onDestroy()
        embedWebView?.destroy()
        player?.release()
        player = null
    }
}
