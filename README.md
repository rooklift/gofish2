# gofish2

Replacement for the original [gofish](https://github.com/rooklift/gofish) library. It does what I need and is much simpler...

Important differences:
* Board coordinates are now zeroth based.
* Boards are not cached at all.
* Various methods have been renamed.
* Colours are now "b", "w", and "" (this is perhaps a bit lame).
* Methods that require a coordinate generally require an SGF-string (e.g. "cc") as such.
