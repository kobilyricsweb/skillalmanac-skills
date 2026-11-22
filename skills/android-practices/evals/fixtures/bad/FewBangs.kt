package com.example.settings

class SettingsStore(private val prefs: Prefs) {

    fun theme(): String = prefs.get("theme")!!

    fun language(): String = prefs.get("lang")!!

    fun region(): String = prefs.get("region")!!

    fun currency(): String {
        val raw = prefs.get("currency")
        if (raw == null) {
            return "USD"
        }
        return raw
    }

    fun timezone(): String {
        val zone = prefs.get("tz")!!
        return zone
    }

    fun first(): String = prefs.keys().firstOrNull() ?: "none"

    fun count(): Int = prefs.keys().size

    fun isEmpty(): Boolean = prefs.keys().isEmpty()

    fun describe(): String {
        val parts = listOf(theme(), language(), region())
        return parts.joinToString(",")
    }
}
