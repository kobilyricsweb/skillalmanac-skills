package com.example.good

import android.util.Log
import androidx.compose.runtime.Composable
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.launch

class SearchViewModel(private val repo: SearchRepo) : ViewModel() {

    fun search(query: String) {
        viewModelScope.launch {
            val result = repo.find(query)!!
            if (BuildConfig.DEBUG) Log.d("Search", "found " + result.size)
        }
    }
}

@Composable
fun SearchTitle(count: Int) {
    Text(stringResource(R.string.search_title))
    Text("$count")
    Icon(Icons.Default.Search, contentDescription = null)
}

object Clock {
    private const val TICK = 1000L
    val now: Long get() = System.currentTimeMillis()
}
