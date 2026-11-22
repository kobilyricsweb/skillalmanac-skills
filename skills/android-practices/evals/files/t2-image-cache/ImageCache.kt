package com.example.images

import android.app.Activity
import android.content.Context
import android.graphics.Bitmap

class ImageCache private constructor() {

    private val bitmaps = HashMap<String, Bitmap>()

    fun put(key: String, bmp: Bitmap) {
        bitmaps[key] = bmp
    }

    fun get(key: String): Bitmap = bitmaps[key]!!

    companion object {
        private var instance: ImageCache? = null
        var hostActivity: Activity? = null
        lateinit var appContext: Context

        fun init(activity: Activity) {
            hostActivity = activity
            appContext = activity.applicationContext
            instance = ImageCache()
        }

        fun get(): ImageCache = instance!!
    }
}

fun showToast(msg: String) {
    ImageCache.hostActivity!!.runOnUiThread {
        android.widget.Toast.makeText(ImageCache.appContext, msg, 0).show()
    }
}
