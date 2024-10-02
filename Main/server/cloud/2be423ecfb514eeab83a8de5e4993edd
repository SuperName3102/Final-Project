SendMode Input  ; Recommended for new scripts due to its superior speed and reliability.
SetWorkingDir %A_ScriptDir%  ; Ensures a consistent starting directory.

`::Suspend

F4::
Stopped := 1
return

F2::
Send {1}
Sleep, 20
Send {2}
Sleep, 20
Send {3}
Sleep, 20
Send {4}
Sleep, 20
Send {5}
Sleep, 20
Send {6}
Sleep, 20
Send {7}
Sleep, 20
Send {8}
return

F3::
Stopped := 0
Loop
{
 Send {8}
 Sleep, 20
 Send {1}
 Sleep, 20
 MouseClick, Left
 if (Stopped = 1)
   break
}
return