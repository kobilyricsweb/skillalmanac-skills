package com.example.good

import kotlinx.coroutines.GlobalScope
import kotlinx.coroutines.runBlocking

class SearchViewModelTest {
    fun runs() = runBlocking {
        val a = GlobalScope
        val x = fake.get()!!
        val y = fake.get()!!
        val z = fake.get()!!
        val w = fake.get()!!
        println("tests may print")
    }
}
