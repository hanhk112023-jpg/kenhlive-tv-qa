package com.kenhlive.tv.ui

import android.content.Intent
import android.os.Bundle
import android.view.KeyEvent
import android.view.View
import android.widget.ImageView
import android.widget.TextView
import androidx.activity.OnBackPressedCallback
import androidx.activity.viewModels
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.fragment.app.Fragment
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import com.google.android.material.bottomnavigation.BottomNavigationView
import com.kenhlive.tv.R
import com.kenhlive.tv.ui.hub.HubFragment
import com.kenhlive.tv.ui.iptv.IptvFragment
import com.kenhlive.tv.ui.movies.MoviesFragment
import com.kenhlive.tv.ui.schedule.ScheduleFragment
import com.kenhlive.tv.ui.search.SearchFragment
import com.kenhlive.tv.ui.settings.SettingsFragment
import com.kenhlive.tv.ui.sports.SportsFragment
import com.kenhlive.tv.ui.sports.SportsViewModel
import com.kenhlive.tv.util.DeviceUtils
import com.kenhlive.tv.util.TvFocusHelper
import kotlinx.coroutines.launch

class MainActivity : AppCompatActivity() {

    companion object {
        const val TAB_SPORTS = 0
        const val TAB_SCHEDULE = 1
        const val TAB_IPTV = 2
        const val TAB_SEARCH = 3
        const val TAB_SETTINGS = 4
        const val TAB_MOVIES = 5
        const val TAB_HUB = 6

        private const val RAIL_ANIM_DURATION_MS = 180L
    }

    private val sportsViewModel: SportsViewModel by viewModels()

    private var isTvMode: Boolean = false
    private var currentTab: Int = TAB_SPORTS
    private var isRailOpen: Boolean = true

    private var tvRailContainer: View? = null
    private var tvRailScrim: View? = null
    private val railTabViews = mutableMapOf<Int, View>()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        isTvMode = DeviceUtils.isTv(this)
        setContentView(R.layout.activity_main)

        if (isTvMode) {
            setupTvRail()
        } else {
            setupPhoneNav()
        }

        setupBackHandler()

        if (savedInstanceState == null) {
            val deepLinkTab = parseDeepLinkTab(intent)
            if (deepLinkTab != null) {
                selectTab(deepLinkTab, hideRailAfter = true)
            } else {
                selectTab(TAB_SPORTS, hideRailAfter = false)
                if (isTvMode) {
                    railTabViews[TAB_SPORTS]?.requestFocus()
                }
            }
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        parseDeepLinkTab(intent)?.let { tab ->
            selectTab(tab, hideRailAfter = true)
        }
    }

    private fun parseDeepLinkTab(intent: Intent?): Int? {
        val data = intent?.data ?: return null
        if (data.scheme == "kenhlive" && data.host == "tab") {
            val seg = data.lastPathSegment?.lowercase() ?: return null
            return when (seg) {
                "0", "sports" -> TAB_SPORTS
                "1", "schedule" -> TAB_SCHEDULE
                "2", "iptv", "tv" -> TAB_IPTV
                "3", "search" -> TAB_SEARCH
                "4", "settings" -> TAB_SETTINGS
                "5", "movies" -> TAB_MOVIES
                "6", "hub" -> TAB_HUB
                else -> null
            }
        }
        return null
    }

    private fun setupTvRail() {
        tvRailContainer = findViewById(R.id.tvRailContainer)
        tvRailScrim = findViewById(R.id.tvRailScrim)

        val entries = listOf(
            Triple(R.id.railTabSports, TAB_SPORTS, Pair(R.drawable.ic_nav_sports, R.string.kl3_nav_sports)),
            Triple(R.id.railTabIptv, TAB_IPTV, Pair(R.drawable.ic_nav_tv, R.string.kl3_nav_iptv)),
            Triple(R.id.railTabMovies, TAB_MOVIES, Pair(R.drawable.ic_nav_movies, R.string.kl3_nav_movies)),
            Triple(R.id.railTabSchedule, TAB_SCHEDULE, Pair(R.drawable.ic_nav_schedule, R.string.kl3_nav_schedule)),
            Triple(R.id.railTabSearch, TAB_SEARCH, Pair(R.drawable.ic_nav_search, R.string.kl3_nav_search)),
            Triple(R.id.railTabSettings, TAB_SETTINGS, Pair(R.drawable.ic_nav_settings, R.string.kl3_nav_settings))
        )

        for ((viewId, tabIndex, iconAndLabel) in entries) {
            val tabView = findViewById<View>(viewId) ?: continue
            railTabViews[tabIndex] = tabView

            tabView.findViewById<ImageView>(R.id.railIcon).setImageResource(iconAndLabel.first)
            tabView.findViewById<TextView>(R.id.railLabel).setText(iconAndLabel.second)
            TvFocusHelper.attachFocusScale(tabView)

            tabView.setOnClickListener {
                selectTab(tabIndex, hideRailAfter = true)
                focusCurrentFragmentContent()
            }

            tabView.setOnKeyListener { _, keyCode, event ->
                if (event.action == KeyEvent.ACTION_DOWN) {
                    when (keyCode) {
                        KeyEvent.KEYCODE_DPAD_RIGHT -> {
                            selectTab(tabIndex, hideRailAfter = true)
                            focusCurrentFragmentContent()
                            true
                        }
                        KeyEvent.KEYCODE_DPAD_CENTER, KeyEvent.KEYCODE_ENTER -> {
                            selectTab(tabIndex, hideRailAfter = true)
                            focusCurrentFragmentContent()
                            true
                        }
                        else -> false
                    }
                } else false
            }
        }

        lifecycleScope.launch {
            repeatOnLifecycle(Lifecycle.State.STARTED) {
                sportsViewModel.uiState.collect { state ->
                    val dot = railTabViews[TAB_SPORTS]?.findViewById<View>(R.id.railLiveDot)
                    dot?.visibility = if (state.hasAnyLive) View.VISIBLE else View.GONE
                }
            }
        }
    }

    private fun setupPhoneNav() {
        val bottomNav = findViewById<BottomNavigationView>(R.id.phoneBottomNav) ?: return
        bottomNav.setOnItemSelectedListener { item ->
            val tab = when (item.itemId) {
                R.id.nav_sports -> TAB_SPORTS
                R.id.nav_iptv -> TAB_IPTV
                R.id.nav_movies -> TAB_MOVIES
                R.id.nav_schedule -> TAB_SCHEDULE
                R.id.nav_search -> TAB_SEARCH
                R.id.nav_settings -> TAB_SETTINGS
                else -> TAB_SPORTS
            }
            selectTab(tab, hideRailAfter = false)
            true
        }
    }

    fun selectTab(tabIndex: Int, hideRailAfter: Boolean = isTvMode) {
        currentTab = tabIndex
        val fragment: Fragment = when (tabIndex) {
            TAB_SPORTS -> SportsFragment()
            TAB_SCHEDULE -> ScheduleFragment()
            TAB_IPTV -> IptvFragment()
            TAB_SEARCH -> SearchFragment()
            TAB_SETTINGS -> SettingsFragment()
            TAB_MOVIES -> MoviesFragment()
            TAB_HUB -> HubFragment()
            else -> SportsFragment()
        }

        supportFragmentManager.beginTransaction()
            .replace(R.id.fragmentContainer, fragment, "tab_$tabIndex")
            .commitAllowingStateLoss()

        if (isTvMode) {
            updateTvRailIndicators()
            if (hideRailAfter) {
                closeTvRail()
            }
        } else {
            val bottomNav = findViewById<BottomNavigationView>(R.id.phoneBottomNav)
            val menuId = when (tabIndex) {
                TAB_SPORTS -> R.id.nav_sports
                TAB_IPTV -> R.id.nav_iptv
                TAB_MOVIES -> R.id.nav_movies
                TAB_SCHEDULE -> R.id.nav_schedule
                TAB_SEARCH -> R.id.nav_search
                TAB_SETTINGS -> R.id.nav_settings
                else -> null
            }
            if (menuId != null && bottomNav != null && bottomNav.selectedItemId != menuId) {
                bottomNav.selectedItemId = menuId
            }
        }
    }

    private fun updateTvRailIndicators() {
        for ((tab, view) in railTabViews) {
            val indicator = view.findViewById<View>(R.id.railIndicator)
            val label = view.findViewById<TextView>(R.id.railLabel)
            val active = tab == currentTab
            indicator?.visibility = if (active) View.VISIBLE else View.INVISIBLE
            label?.setTextColor(
                ContextCompat.getColor(
                    this,
                    if (active) R.color.kl3_text_primary else R.color.kl3_text_secondary
                )
            )
        }
    }

    fun openTvRail() {
        if (!isTvMode) return
        isRailOpen = true
        tvRailScrim?.visibility = View.VISIBLE
        tvRailScrim?.animate()?.alpha(1f)?.setDuration(RAIL_ANIM_DURATION_MS)?.start()
        tvRailContainer?.visibility = View.VISIBLE
        tvRailContainer?.animate()?.translationX(0f)?.setDuration(RAIL_ANIM_DURATION_MS)?.withEndAction {
            (railTabViews[currentTab] ?: railTabViews[TAB_SPORTS])?.requestFocus()
        }?.start()
    }

    fun closeTvRail() {
        if (!isTvMode) return
        isRailOpen = false
        val rail = tvRailContainer ?: return
        val width = rail.width.takeIf { it > 0 }?.toFloat()
            ?: resources.getDimension(R.dimen.kl3_rail_width)
        rail.animate()
            .translationX(-width)
            .setDuration(RAIL_ANIM_DURATION_MS)
            .withEndAction { rail.visibility = View.GONE }
            .start()
        tvRailScrim?.animate()
            ?.alpha(0f)
            ?.setDuration(RAIL_ANIM_DURATION_MS)
            ?.withEndAction { tvRailScrim?.visibility = View.GONE }
            ?.start()
    }

    private fun focusCurrentFragmentContent() {
        findViewById<View>(R.id.fragmentContainer)?.post {
            val frag = supportFragmentManager.findFragmentById(R.id.fragmentContainer)
            when (frag) {
                is SportsFragment -> frag.focusContent()
                is ScheduleFragment -> frag.focusContent()
                is IptvFragment -> frag.focusContent()
                is MoviesFragment -> frag.focusContent()
                is SearchFragment -> frag.focusContent()
                is SettingsFragment -> frag.focusContent()
                is HubFragment -> frag.focusContent()
            }
        }
    }

    private fun setupBackHandler() {
        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                if (!isTvMode) {
                    if (currentTab != TAB_SPORTS) {
                        selectTab(TAB_SPORTS, hideRailAfter = false)
                    } else {
                        showExitDialog()
                    }
                    return
                }

                // TV 3-tier BACK key handling:
                // Tier 1 (Player/Dialog) handled by PlayerActivity/AlertDialog itself.
                // Tier 2: Inside tab content while rail is closed -> open rail and focus current tab.
                if (!isRailOpen) {
                    openTvRail()
                    return
                }

                // Tier 3: Rail is open -> if not Tab 0, return to Tab 0; if on Tab 0, show exit dialog.
                if (currentTab != TAB_SPORTS) {
                    selectTab(TAB_SPORTS, hideRailAfter = false)
                    railTabViews[TAB_SPORTS]?.requestFocus()
                } else {
                    showExitDialog()
                }
            }
        })
    }

    private fun showExitDialog() {
        AlertDialog.Builder(this)
            .setTitle(R.string.kl3_exit_title)
            .setMessage(R.string.kl3_exit_message)
            .setNegativeButton(R.string.kl3_exit_stay, null)
            .setPositiveButton(R.string.kl3_exit_confirm) { _, _ -> finish() }
            .show()
    }
}
