package com.example.profile

import android.util.Log
import androidx.compose.runtime.Composable

@Composable
fun ProfileScreen(viewModel: ProfileViewModel) {
    val state = viewModel.state.collectAsState().value
    Log.d("Profile", "render " + state)
    Column {
        Text("My profile")
        Image(painter = avatar(state.avatarUrl!!), contentDescription = "Avatar")
        Text(text = state.user!!.displayName!!)
        Button(onClick = { viewModel.save() }) {
            Text("Save changes")
        }
        IconButton(onClick = { viewModel.share() }) {
            Icon(Icons.Default.Share, contentDescription = null)
        }
    }
}
