package com.example.net

import android.util.Log

class Api(private val client: Client) {

    fun load(id: String) {
        Log.d(TAG, "loading " + id)
        Log.v(TAG, "verbose")
        if (BuildConfig.DEBUG) Log.d(TAG, "guarded on the same line")
        if (BuildConfig.DEBUG) {
            Log.d(TAG, "guarded one line above")
        }
        Log.e(TAG, "errors are fine")
        // Log.d(TAG, "a comment is silent")
        println("debug output")
        try {
            client.get(id)
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    fun far() {
        if (BuildConfig.DEBUG) {
            val a = 1
            val b = 2
            val c = 3
            val d = 4
            val e = 5
            Log.d(TAG, "guard is more than four lines above")
        }
    }

    companion object {
        private const val TAG = "Api"
    }
}
