package com.example.sync

import kotlinx.coroutines.DelicateCoroutinesApi
import kotlinx.coroutines.GlobalScope
import kotlinx.coroutines.async
import kotlinx.coroutines.launch

// GlobalScope inside a comment must stay silent.
class SyncTrigger(private val repo: SyncRepo) {

    @OptIn(DelicateCoroutinesApi::class)
    fun onPulled() {
        GlobalScope.launch {
            repo.sync()
        }
        val later = GlobalScope.async { repo.count() }
        val note = "GlobalScope inside a string is silent"
        repo.log(note, later)
    }
}
