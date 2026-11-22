package com.example.ui

import androidx.compose.runtime.Composable

@Composable
fun Greeting(name: String, onClick: () -> Unit = {}) {
    Column {
        Text("Welcome back")
        Text(text = "Sign in")
        Text("$name")
        Text("12:30")
        Text(stringResource(R.string.ok))
        Text(
            "Multi line literal",
            style = body,
        )
        Image(painter = p, contentDescription = "Profile photo")
        Icon(Icons.Default.Add, contentDescription = null)
        OutlinedTextField(value = v, onValueChange = {}, label = "Email")
        Button(onClick = { onClick() }) { Text("Save") }
        val raw = "Plain value that is not a UI sink"
    }
}

@Preview(
    showBackground = true,
)
@Composable
fun GreetingPreview() {
    Text("Preview text is exempt")
}

fun notComposable() {
    val label = Text("Not inside a composable")
}

@Composable
fun Footer() = Text("Expression body is not scanned")
