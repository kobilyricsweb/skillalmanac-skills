package com.example.profile

import androidx.lifecycle.ViewModel
import kotlinx.coroutines.runBlocking

class ProfileViewModel(private val repo: ProfileRepo) : ViewModel() {

    fun loadNow(): Profile {
        return runBlocking { repo.fetch() }
    }

    // runBlocking in a comment is silent.
    fun label() = "runBlocking in a string is silent"
}
