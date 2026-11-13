package com.kenhlive.tv.ui.movies

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.kenhlive.tv.model.MovieItem
import com.kenhlive.tv.repository.MovieRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class MoviesUiState(
    val isLoading: Boolean = false,
    val movies: List<MovieItem> = emptyList()
)

class MoviesViewModel(
    private val repository: MovieRepository = MovieRepository()
) : ViewModel() {

    private val _uiState = MutableStateFlow(MoviesUiState(isLoading = true))
    val uiState: StateFlow<MoviesUiState> = _uiState.asStateFlow()

    init {
        load()
    }

    fun load() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true)
            val list = runCatching { repository.fetchLatestMovies(1) }.getOrElse { emptyList() }
            _uiState.value = MoviesUiState(isLoading = false, movies = list)
        }
    }
}
