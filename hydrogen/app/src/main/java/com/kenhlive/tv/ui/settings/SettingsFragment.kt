package com.kenhlive.tv.ui.settings

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.view.KeyEvent
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import coil.imageLoader
import com.kenhlive.tv.BuildConfig
import com.kenhlive.tv.databinding.FragmentSettingsBinding
import com.kenhlive.tv.logic.VersionComparator
import com.kenhlive.tv.network.HttpClientProvider
import com.kenhlive.tv.ui.MainActivity
import com.kenhlive.tv.util.DeviceUtils
import com.kenhlive.tv.util.TvFocusHelper

class SettingsFragment : Fragment() {

    private var _binding: FragmentSettingsBinding? = null
    private val binding get() = _binding!!

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentSettingsBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        val isTv = DeviceUtils.isTv(requireContext())

        binding.tvAppVersion.text = "Phiên bản hiện tại: ${BuildConfig.VERSION_NAME} (build ${BuildConfig.VERSION_CODE})"

        val buttons = listOf(
            binding.btnCheckUpdate,
            binding.btnClearCache,
            binding.btnReportBug,
            binding.btnOpenHub
        )
        buttons.forEach { btn ->
            if (isTv) TvFocusHelper.attachFocusScale(btn)
            btn.setOnKeyListener { _, keyCode, event ->
                if (isTv && event.action == KeyEvent.ACTION_DOWN && keyCode == KeyEvent.KEYCODE_DPAD_LEFT) {
                    (activity as? MainActivity)?.openTvRail()
                    true
                } else false
            }
        }

        binding.btnCheckUpdate.setOnClickListener {
            // Fail-closed version check against current BuildConfig.VERSION_NAME
            val current = BuildConfig.VERSION_NAME
            val remoteSample: String? = null
            val hasUpdate = VersionComparator.isNewerVersion(remoteSample, current)
            binding.tvSettingsStatus.text = if (hasUpdate) {
                "Đã có phiên bản mới: $remoteSample"
            } else {
                "Bạn đang dùng phiên bản mới nhất ($current) hoặc chưa có thông tin bản mới."
            }
        }

        binding.btnClearCache.setOnClickListener {
            HttpClientProvider.clearCache()
            requireContext().imageLoader.memoryCache?.clear()
            binding.tvSettingsStatus.text = "Đã xoá bộ nhớ đệm (HTTP & ảnh)."
        }

        binding.btnReportBug.setOnClickListener {
            val intent = Intent(Intent.ACTION_VIEW, Uri.parse("https://t.me/kenhlivetv"))
            runCatching { startActivity(intent) }
        }

        binding.btnOpenHub.setOnClickListener {
            (activity as? MainActivity)?.selectTab(MainActivity.TAB_HUB, hideRailAfter = true)
        }
    }

    fun focusContent(): Boolean = _binding?.btnCheckUpdate?.requestFocus() ?: false

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
