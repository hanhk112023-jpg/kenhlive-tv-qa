package com.kenhlive.tv.ui.sports

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.kenhlive.tv.model.MatchModel
import com.kenhlive.tv.model.MatchState
import com.kenhlive.tv.repository.SportsRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class SportsUiState(
    val isLoading: Boolean = false,
    val matches: List<MatchModel> = emptyList(),
    val heroMatch: MatchModel? = null,
    val hasAnyLive: Boolean = false,
    val error: String? = null
)

class SportsViewModel(
    private val repository: SportsRepository = SportsRepository()
) : ViewModel() {

    private val _uiState = MutableStateFlow(SportsUiState(isLoading = true))
    val uiState: StateFlow<SportsUiState> = _uiState.asStateFlow()

    init {
        refresh()
    }

    fun refresh() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)
            val list = runCatching { repository.fetchAllMatches() }.getOrElse { emptyList() }
            val liveMatches = list.filter { it.state == MatchState.LIVE }
            val hero = liveMatches.firstOrNull { it.isFeatured }
                ?: liveMatches.firstOrNull()
                ?: list.firstOrNull()

            _uiState.value = SportsUiState(
                isLoading = false,
                matches = list,
                heroMatch = hero,
                hasAnyLive = liveMatches.isNotEmpty()
            )
        }
    }
}
