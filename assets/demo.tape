Output assets/demo.gif

Set Shell "bash"
Set FontSize 15
Set Width 1200
Set Height 680
Set Theme "Dracula"
Set Padding 20
Set TypingSpeed 45ms
Set PlaybackSpeed 1.0

Type "python3 skill/scripts/critical_path.py examples/tasks.json --outdir /tmp/critical-path-demo"
Enter
Sleep 1500ms

Type "ls /tmp/critical-path-demo"
Enter
Sleep 1500ms

Type "cat /tmp/critical-path-demo/critical_path.md"
Enter
Sleep 4500ms
