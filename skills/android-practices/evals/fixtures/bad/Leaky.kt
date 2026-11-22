package com.example.cache

import android.content.Context

object ImageCache {
    var appContext: Context? = null
    lateinit var activity: MainActivity
    private val cache = HashMap<String, Bitmap>()

    fun init(c: Context) {
        val local: Context = c
        cache.clear()
    }
}

class Repo {
    companion object {
        private var instance: Repo? = null
        var currentView: View? = null
        private lateinit var ctx: Context
    }

    var fine: Context? = null
}

var topLevelFragment: Fragment? = null
