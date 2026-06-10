import lldb
import traceback
import threading

def log(message: str):
    print(message, flush=True)
    with open("/tmp/lldb.log", "a+") as log:
        log.write(message + "\n")


def firstStoppedThread(process: lldb.SBProcess) -> lldb.SBThread:
    for i in range(0, process.GetNumThreads()):
        thread: lldb.SBThread = process.GetThreadAtIndex(i)
        reason: lldb.StopReason = thread.GetStopReason()

        if (reason == lldb.eStopReasonBreakpoint or
            reason == lldb.eStopReasonException or
            reason == lldb.eStopReasonPlanComplete or
            reason == lldb.eStopReasonSignal or
            reason == lldb.eStopReasonWatchpoint
        ):
            return thread

    return None


def wantAutoContinue(frame: lldb.SBFrame) -> tuple:
    funcname = frame.GetFunctionName()
    thread: lldb.SBThread = frame.GetThread()

    if thread.GetStopReason() == lldb.eStopReasonSignal:
        siginfo: lldb.SBValue = thread.GetSiginfo()

        num = siginfo.GetChildMemberWithName("si_signo").GetValue()
        code = siginfo.GetChildMemberWithName("si_code").GetValue()

        segfault_addr = siginfo\
            .GetChildMemberWithName("_sifields") \
            .GetChildMemberWithName("_sigfault") \
            .GetChildMemberWithName("si_addr") \
            .GetValue()
        
        if not segfault_addr:
            segfault_addr = "0x0"

        if num == "11" and code == "1" and int(segfault_addr, 16) == 0:
            return (True, "SIGSEGV with code SEGV_MAPERR and segfault address is 0")
        elif num == "7" and code == "2":
            return (True, "SIGBUS with code BUS_ADRERR")

    if thread.GetName().startswith("binder:"):
        return (True, "thread name related to binder")

    if not funcname:
        return (False, "no function name")

    if funcname.startswith('java.'):
        return (True, "func name starts with \"java.\"")

    if funcname.startswith('android.'):
        return (True, "func name starts with \"android.\"")

    if funcname.startswith('com.android.'):
        return (True, "func name starts with \"com.android.\"")

    if funcname.startswith('jdk.'):
        return (True, "func name starts with \"jdk.\"")

    if funcname.startswith('sun.'):
        return (True, "func name starts with \"sun.\"")

    if funcname.startswith('__jit_'):
        return (True, "func name starts with \"__jit_\"")

    return (False, "")


def loop(debugger: lldb.SBDebugger, listener: lldb.SBListener, process: lldb.SBProcess):
    while True:
        if debugger.GetSelectedTarget().GetProcess().GetState() == lldb.eStateExited:
            break

        try:
            event = lldb.SBEvent()
            res = listener.WaitForEvent(1, event)

            if not res:
                continue

            if not lldb.SBProcess.EventIsProcessEvent(event):
                continue

            state = lldb.SBProcess.GetStateFromEvent(event)

            if not state:
                continue

            stoppedThread = firstStoppedThread(process)

            if not stoppedThread:
                continue

            frame: lldb.SBFrame = stoppedThread.GetFrameAtIndex(0)

            shouldContinue, reason = wantAutoContinue(frame)
            if shouldContinue:
                # log(f"Auto-continue because {reason}")
                process.Continue()
        except Exception:
            traceback.print_exc()
            break


def __lldb_init_module(debugger: lldb.SBDebugger, internal_dict):
    listener = lldb.SBListener('my_debugger_loop')
    process = debugger.GetSelectedTarget().GetProcess()
    process.GetBroadcaster().AddListener(listener, 0xffffffff)

    s = threading.Thread(target=loop, args=(debugger, listener, process))
    s.start()
