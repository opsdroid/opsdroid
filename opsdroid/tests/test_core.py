import os
import signal
import threading

import asynctest.mock as amock
import pytest

from opsdroid.core import OpsDroid


@pytest.mark.skipif(os.name == "nt", reason="SIGHUP unsupported on windows")
@pytest.mark.isolate_signal_test
def test_signals(event_loop):
    pid = os.getpid()

    def send_signal(sig):
        # print(f"{pid} <== {sig}")
        os.kill(pid, sig)

    with OpsDroid() as opsdroid:
        opsdroid.load = amock.CoroutineMock()
        # bypass task creation in start() and just run the task loop
        opsdroid.start = amock.CoroutineMock(return_value=opsdroid._run_tasks)
        opsdroid.unload = amock.CoroutineMock()
        opsdroid.reload = amock.CoroutineMock()
        threading.Timer(2, lambda: send_signal(signal.SIGHUP)).start()
        threading.Timer(3, lambda: send_signal(signal.SIGINT)).start()
        with pytest.raises(SystemExit):
            opsdroid.run()
        assert opsdroid.reload.called
