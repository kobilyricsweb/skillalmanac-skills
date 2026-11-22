package com.example.cart

class CartMapper {

    fun total(cart: Cart?): Long {
        val a = cart!!.items!!.size
        val b = cart!!.owner!!.name!!.length
        val c = cart.lookup("x")!!
        val d = cart.lookup("y")!!
        val e = cart.lookup("z")!!
        val same = a != b
        val note = "done!! really"
        // a comment with !! is silent
        return (a + b + c + d + e).toLong() + if (!same) 1 else 0
    }
}
