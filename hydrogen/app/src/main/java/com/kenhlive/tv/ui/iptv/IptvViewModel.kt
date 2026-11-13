package com.kenhlive.tv.ui.iptv

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.kenhlive.tv.model.EpgProgram
import com.kenhlive.tv.model.IptvChannel
import com.kenhlive.tv.repository.IptvRepository
import kotlinx.coroutines.async
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class IptvUiState(
    val isLoading: Boolean = false,
    val channels: List<IptvChannel> = emptyList(),
    val epgMap: Map<String, EpgProgram> = emptyMap()
)

class IptvViewModel(
    private val repository: IptvRepository = IptvRepository()
) : ViewModel() {

    private val _uiState = MutableStateFlow(IptvUiState(isLoading = true))
    val uiState: StateFlow<IptvUiState> = _uiState.asStateFlow()

    init {
        load()
    }

    fun load() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true)
            val chDeferred = async { runCatching { repository.fetchChannels() }.getOrElse { emptyList() } }
            val epgDeferred = async { runCatching { repository.fetchCurrentEpgMap() }.getOrElse { emptyMap() } }
            _uiState.value = IptvUiState(
                isLoading = false,
                channels = chDeferred.await(),
                epgMap = epgDeferred.await()
            )
        }
    }
}
