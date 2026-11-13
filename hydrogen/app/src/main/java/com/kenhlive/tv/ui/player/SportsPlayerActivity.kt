package com.kenhlive.tv.ui.player

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.view.View
import android.widget.Button
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
import com.kenhlive.tv.model.MatchModel
import com.kenhlive.tv.model.MatchState
import com.kenhlive.tv.util.DeviceUtils
import com.kenhlive.tv.util.TvFocusHelper

class SportsPlayerActivity : AppCompatActivity() {

    companion object {
        private const val EXTRA_SCOREBOARD = "extra_scoreboard"
        private const val EXTRA_MINUTE = "extra_minute"
        private const val EXTRA_STATE = "extra_state"
        private const val EXTRA_URLS = "extra_urls"
        private const val EXTRA_LABELS = "extra_labels"

        fun start(context: Context, match: MatchModel) {
            val scoreText = "${match.homeTeam}  ${match.displayScoreOrVs()}  ${match.awayTeam}"
            val minuteText = match.minuteText ?: when (match.state) {
                MatchState.LIVE -> "LIVE"
                MatchState.UPCOMING -> "SẮP ĐÁ"
                MatchState.FINISHED -> "FT"
            }
            val intent = Intent(context, SportsPlayerActivity::class.java).apply {
                putExtra(EXTRA_SCOREBOARD, scoreText)
                putExtra(EXTRA_MINUTE, minuteText)
                putExtra(EXTRA_STATE, match.state.name)
                putStringArrayListExtra(EXTRA_URLS, ArrayList(match.streams.map { it.streamUrl }))
                putStringArrayListExtra(EXTRA_LABELS, ArrayList(match.streams.map { it.label }))
            }
            context.startActivity(intent)
        }
    }

    private var player: ExoPlayer? = null
    private lateinit var playerView: PlayerView
    private lateinit var tvError: TextView
    private lateinit var tvSourceLabel: TextView
    private lateinit var btnPlayPause: Button

    private var streamUrls: List<String> = emptyList()
    private var streamLabels: List<String> = emptyList()
    private var currentIndex = 0

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_player_sports)

        playerView = findViewById(R.id.playerView)
        tvError = findViewById(R.id.tvSportsPlayerError)
        tvSourceLabel = findViewById(R.id.tvSportsSourceLabel)
        btnPlayPause = findViewById(R.id.btnSportsPlayPause)
        val btnSwitch = findViewById<Button>(R.id.btnSportsSwitchSource)
        val btnOptions = findViewById<Button>(R.id.btnSportsOptions)
        val tvBadge = findViewById<TextView>(R.id.tvSportsStateBadge)
        val tvScoreboard = findViewById<TextView>(R.id.tvSportsMatchScoreboard)
        val tvMinute = findViewById<TextView>(R.id.tvSportsMinute)

        tvScoreboard.text = intent.getStringExtra(EXTRA_SCOREBOARD) ?: ""
        tvMinute.text = intent.getStringExtra(EXTRA_MINUTE) ?: ""
        val state = runCatching { MatchState.valueOf(intent.getStringExtra(EXTRA_STATE) ?: "LIVE") }
            .getOrDefault(MatchState.LIVE)
        tvBadge.setBackgroundResource(
            when (state) {
                MatchState.LIVE -> R.drawable.kl3_badge_live
                MatchState.UPCOMING -> R.drawable.kl3_badge_upcoming
                MatchState.FINISHED -> R.drawable.kl3_badge_finished
            }
        )
        tvBadge.text = when (state) {
            MatchState.LIVE -> getString(R.string.kl3_badge_live)
            MatchState.UPCOMING -> getString(R.string.kl3_badge_upcoming)
            MatchState.FINISHED -> getString(R.string.kl3_badge_finished)
        }

        streamUrls = intent.getStringArrayListExtra(EXTRA_URLS) ?: emptyList()
        streamLabels = intent.getStringArrayListExtra(EXTRA_LABELS) ?: emptyList()

        if (DeviceUtils.isTv(this)) {
            listOf(btnPlayPause, btnSwitch, btnOptions).forEach { TvFocusHelper.attachFocusScale(it) }
            btnPlayPause.requestFocus()
        }

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

        btnSwitch.setOnClickListener { showSourcePicker() }
        btnOptions.setOnClickListener { showOptions() }

        initPlayer()
        if (streamUrls.isEmpty()) {
            showError("Trận đấu này chưa có luồng phát trực tiếp.")
        } else {
            playIndex(0)
        }
    }

    private fun initPlayer() {
        player = ExoPlayerFactory.create(this).also { exo ->
            playerView.player = exo
            exo.addListener(object : Player.Listener {
                override fun onPlayerError(error: PlaybackException) {
                    showError("Lỗi phát luồng thể thao (${error.errorCodeName}). Hãy thử đổi nguồn BLV.")
                }
            })
        }
    }

    private fun playIndex(index: Int) {
        val url = streamUrls.getOrNull(index) ?: return
        currentIndex = index
        tvError.visibility = View.GONE
        tvSourceLabel.text = streamLabels.getOrNull(index) ?: "Nguồn ${index + 1}"

        val exo = player ?: return
        val factory = DefaultHttpDataSource.Factory()
            .setUserAgent("KenhLive/0.1.12 (Android)")
            .setAllowCrossProtocolRedirects(true)

        if (url.contains(".m3u8", ignoreCase = true)) {
            exo.setMediaSource(HlsMediaSource.Factory(factory).createMediaSource(MediaItem.fromUri(url)))
        } else {
            exo.setMediaItem(MediaItem.fromUri(url))
        }
        exo.prepare()
        exo.playWhenReady = true
    }

    private fun showSourcePicker() {
        if (streamUrls.isEmpty()) return
        val labels = streamLabels.ifEmpty { streamUrls.indices.map { "Nguồn ${it + 1}" } }
        AlertDialog.Builder(this)
            .setTitle(R.string.kl3_player_sources)
            .setSingleChoiceItems(labels.toTypedArray(), currentIndex) { d, idx ->
                playIndex(idx)
                d.dismiss()
            }
            .show()
    }

    private fun showOptions() {
        val opts = arrayOf("Bám sát trực tiếp (Live edge)", "Tỉ lệ khung hình (Vừa / Đầy)", "Tải lại luồng")
        AlertDialog.Builder(this)
            .setTitle(R.string.kl3_player_options)
            .setItems(opts) { _, which ->
                when (which) {
                    0 -> player?.seekToDefaultPosition()
                    1 -> playerView.resizeMode =
                        if (playerView.resizeMode == AspectRatioFrameLayout.RESIZE_MODE_FIT)
                            AspectRatioFrameLayout.RESIZE_MODE_ZOOM else AspectRatioFrameLayout.RESIZE_MODE_FIT
                    2 -> playIndex(currentIndex)
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
