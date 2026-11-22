package com.example.export

import kotlinx.coroutines.runBlocking

class Exporter(private val source: DataSource) {

    fun exportAll(): List<Row> = runBlocking {
        source.rows()
    }
}
