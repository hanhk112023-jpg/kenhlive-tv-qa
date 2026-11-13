package com.kenhlive.tv.ui.player

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.view.KeyEvent
import android.view.View
import android.widget.Button
import android.widget.ImageView
import android.widget.ProgressBar
import android.widget.TextView
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import androidx.media3.common.MediaItem
import androidx.media3.common.PlaybackException
import androidx.media3.common.Player
import androidx.media3.datasource.DefaultHttpDataSource
import androidx.media3.datasource.HttpDataSource
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.exoplayer.hls.HlsMediaSource
import androidx.media3.ui.AspectRatioFrameLayout
import androidx.media3.ui.PlayerView
import coil.load
import coil.size.Precision
import com.kenhlive.tv.R
import com.kenhlive.tv.model.IptvChannel
import com.kenhlive.tv.repository.IptvRepository
import com.kenhlive.tv.util.DeviceUtils
import com.kenhlive.tv.util.TvFocusHelper
import kotlinx.coroutines.launch

class TvPlayerActivity : AppCompatActivity() {

    companion object {
        private const val EXTRA_INDEX = "extra_index"
        private const val EXTRA_NAMES = "extra_names"
        private const val EXTRA_URLS = "extra_urls"
        private const val EXTRA_LOGOS = "extra_logos"
        private const val EXTRA_EPGS = "extra_epgs"
        private const val EXTRA_EPG_PROGRESS = "extra_epg_progress"
        private const val EXTRA_GEOBLOCK = "extra_geoblock"

        fun start(
            context: Context,
            channels: List<IptvChannel>,
            selectedIndex: Int,
            epgTitles: List<String>,
            epgProgress: List<Int>
        ) {
            val intent = Intent(context, TvPlayerActivity::class.java).apply {
                putExtra(EXTRA_INDEX, selectedIndex)
                putStringArrayListExtra(EXTRA_NAMES, ArrayList(channels.map { it.name }))
                putStringArrayListExtra(EXTRA_URLS, ArrayList(channels.map { it.streamUrl }))
                putStringArrayListExtra(EXTRA_LOGOS, ArrayList(channels.map { it.logoUrl ?: "" }))
                putStringArrayListExtra(EXTRA_EPGS, ArrayList(epgTitles))
                putIntegerArrayListExtra(EXTRA_EPG_PROGRESS, ArrayList(epgProgress))
                putExtra(EXTRA_GEOBLOCK, BooleanArray(channels.size) { channels[it].isGeoBlockedSuspected })
            }
            context.startActivity(intent)
        }
    }

    private var player: ExoPlayer? = null
    private lateinit var playerView: PlayerView
    private lateinit var ivLogo: ImageView
    private lateinit var tvTitle: TextView
    private lateinit var tvEpgNow: TextView
    private lateinit var progressEpg: ProgressBar
    private lateinit var tvError: TextView

    private val iptvRepo = IptvRepository()
    private var names: List<String> = emptyList()
    private var urls: List<String> = emptyList()
    private var logos: List<String> = emptyList()
    private var epgs: List<String> = emptyList()
    private var epgProgress: List<Int> = emptyList()
    private var geoFlags: BooleanArray = BooleanArray(0)
    private var currentIndex = 0

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_player_tv)

        playerView = findViewById(R.id.playerView)
        ivLogo = findViewById(R.id.ivTvChannelLogo)
        tvTitle = findViewById(R.id.tvChannelTitle)
        tvEpgNow = findViewById(R.id.tvChannelEpgNow)
        progressEpg = findViewById(R.id.progressTvEpg)
        tvError = findViewById(R.id.tvPlayerError)

        val btnPrev = findViewById<Button>(R.id.btnPrevChannel)
        val btnNext = findViewById<Button>(R.id.btnNextChannel)
        val btnList = findViewById<Button>(R.id.btnChannelList)
        val btnOptions = findViewById<Button>(R.id.btnTvOptions)

        names = intent.getStringArrayListExtra(EXTRA_NAMES) ?: emptyList()
        urls = intent.getStringArrayListExtra(EXTRA_URLS) ?: emptyList()
        logos = intent.getStringArrayListExtra(EXTRA_LOGOS) ?: emptyList()
        epgs = intent.getStringArrayListExtra(EXTRA_EPGS) ?: emptyList()
        epgProgress = intent.getIntegerArrayListExtra(EXTRA_EPG_PROGRESS) ?: emptyList()
        geoFlags = intent.getBooleanArrayExtra(EXTRA_GEOBLOCK) ?: BooleanArray(names.size)
        currentIndex = intent.getIntExtra(EXTRA_INDEX, 0).coerceIn(0, (names.size - 1).coerceAtLeast(0))

        if (DeviceUtils.isTv(this)) {
            listOf(btnPrev, btnNext, btnList, btnOptions).forEach { TvFocusHelper.attachFocusScale(it) }
            btnList.requestFocus()
        }

        btnPrev.setOnClickListener { zapChannel(-1) }
        btnNext.setOnClickListener { zapChannel(1) }
        btnList.setOnClickListener { showChannelListDialog() }
        btnOptions.setOnClickListener { showOptions() }

        initPlayer()
        if (urls.isNotEmpty()) {
            playChannel(currentIndex)
        } else {
            showError("Không có kênh truyền hình nào để phát.")
        }
    }

    override fun onKeyDown(keyCode: Int, event: KeyEvent?): Boolean {
        if (keyCode == KeyEvent.KEYCODE_CHANNEL_UP) {
            zapChannel(1)
            return true
        }
        if (keyCode == KeyEvent.KEYCODE_CHANNEL_DOWN) {
            zapChannel(-1)
            return true
        }
        return super.onKeyDown(keyCode, event)
    }

    private fun zapChannel(delta: Int) {
        if (urls.isEmpty()) return
        val next = (currentIndex + delta + urls.size) % urls.size
        playChannel(next)
    }

    private fun initPlayer() {
        player = ExoPlayerFactory.create(this).also { exo ->
            playerView.player = exo
            exo.addListener(object : Player.Listener {
                override fun onPlayerError(error: PlaybackException) {
                    val cause = error.cause
                    val isHttpDenied = cause is HttpDataSource.InvalidResponseCodeException &&
                        (cause.responseCode == 403 || cause.responseCode == 451)
                    val suspected = geoFlags.getOrNull(currentIndex) == true
                    if (suspected || isHttpDenied) {
                        showError(getString(R.string.kl3_player_geoblock))
                    } else {
                        showError("Không thể phát kênh này (${error.errorCodeName}).")
                    }
                }
            })
        }
    }

    private fun playChannel(index: Int) {
        currentIndex = index
        tvError.visibility = View.GONE
        tvTitle.text = names.getOrNull(index) ?: ""
        tvEpgNow.text = epgs.getOrNull(index)?.ifBlank { "Phát trực tiếp 24/7" } ?: "Phát trực tiếp 24/7"
        val pct = epgProgress.getOrNull(index) ?: 0
        progressEpg.visibility = if (pct > 0) View.VISIBLE else View.GONE
        progressEpg.progress = pct
        ivLogo.load(logos.getOrNull(index)?.ifBlank { null }) {
            size(112, 88)
            precision(Precision.INEXACT)
        }

        val rawUrl = urls.getOrNull(index) ?: return
        lifecycleScope.launch {
            val resolved = iptvRepo.resolvePlayableStreamUrl(rawUrl)
            val exo = player ?: return@launch
            val factory = DefaultHttpDataSource.Factory()
                .setUserAgent("KenhLive/0.1.12 (Android)")
                .setAllowCrossProtocolRedirects(true)

            if (resolved.contains(".m3u8", ignoreCase = true)) {
                exo.setMediaSource(HlsMediaSource.Factory(factory).createMediaSource(MediaItem.fromUri(resolved)))
            } else {
                exo.setMediaItem(MediaItem.fromUri(resolved))
            }
            exo.prepare()
            exo.playWhenReady = true
        }
    }

    private fun showChannelListDialog() {
        if (names.isEmpty()) return
        AlertDialog.Builder(this)
            .setTitle("Danh sách kênh TV")
            .setSingleChoiceItems(names.toTypedArray(), currentIndex) { d, idx ->
                playChannel(idx)
                d.dismiss()
            }
            .show()
    }

    private fun showOptions() {
        val opts = arrayOf("Tỉ lệ khung hình (Vừa / Đầy)", "Tải lại kênh")
        AlertDialog.Builder(this)
            .setTitle(R.string.kl3_player_options)
            .setItems(opts) { _, which ->
                when (which) {
                    0 -> playerView.resizeMode =
                        if (playerView.resizeMode == AspectRatioFrameLayout.RESIZE_MODE_FIT)
                            AspectRatioFrameLayout.RESIZE_MODE_ZOOM else AspectRatioFrameLayout.RESIZE_MODE_FIT
                    1 -> playChannel(currentIndex)
                }
            }
            .show()
    }

    private fun showError(msg: String) {
        tvError.text = msg
        tvError.visibility = View.VISIBLE
    }

    override fun onStop() {
        super.onStop()
        player?.pause()
    }

    override fun onDestroy() {
        super.onDestroy()
        player?.release()
        player = null
    }
}
