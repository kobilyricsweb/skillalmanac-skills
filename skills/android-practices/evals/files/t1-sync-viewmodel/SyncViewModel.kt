package com.example.sync

import android.util.Log
import androidx.lifecycle.ViewModel
import kotlinx.coroutines.DelicateCoroutinesApi
import kotlinx.coroutines.GlobalScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking

class SyncViewModel(private val repo: SyncRepository) : ViewModel() {

    private val _state = MutableStateFlow(SyncState.Idle)
    val state: StateFlow<SyncState> = _state

    // Called from the refresh button on the main thread.
    fun onRefreshClicked() {
        Log.d("Sync", "refresh clicked")
        val cached = runBlocking { repo.readCache() }
        _state.value = SyncState.Showing(cached)
        startBackgroundSync()
    }

    @OptIn(DelicateCoroutinesApi::class)
    private fun startBackgroundSync() {
        GlobalScope.launch {
            _state.value = SyncState.Loading
            val fresh = repo.pullFromServer()
            Log.d("Sync", "pulled " + fresh.size + " rows")
            _state.value = SyncState.Showing(fresh)
        }
    }
}
