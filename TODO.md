1. switch over from TOML to JSON
2. every pre-commit, you format all json files and turn any special unicode characters into backslash escapes
3. roblox understands this and immediately converts to normal Unicode when receiving through Http
4. can't use escapes in TOML since the language string syntax does NOT support it...
5. rip, i really wanted to use tomls
6. figure out how pyproject.toml dependencies and python project building actually works