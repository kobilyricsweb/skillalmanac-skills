# Scenario

We are a 40-person company. We want a shared MCP server that lets everyone's assistants read and update our project tracker (a hosted SaaS with per-user permissions). Staff use laptops and some phones. Our security lead says nobody may paste long-lived tokens into config files. Right now the prototype is a stdio server that reads one admin token from an environment variable, and it also has a tool called `run_query` that takes a raw query string. The prototype's README has the admin token in an example.

Tell us what to change.
