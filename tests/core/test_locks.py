"""Tests for the reader-writer lock."""
import threading
import time

from app.core.locks import RWLock


def run_in_thread(fn):
    thread = threading.Thread(target=fn, daemon=True)
    thread.start()
    return thread


class TestRWLock:

    def test_readers_share_the_lock(self):
        lock = RWLock()
        both_inside = threading.Barrier(2, timeout=2)
        errors = []

        def reader():
            with lock.read_lock():
                try:
                    both_inside.wait()  # only passes if two readers hold the lock at once
                except threading.BrokenBarrierError as e:
                    errors.append(e)

        threads = [run_in_thread(reader) for _ in range(2)]
        for t in threads:
            t.join(3)

        assert errors == []

    def test_writer_waits_for_reader(self):
        lock = RWLock()
        events = []
        reader_inside = threading.Event()
        release_reader = threading.Event()

        def reader():
            with lock.read_lock():
                reader_inside.set()
                release_reader.wait(2)
                events.append("reader done")

        def writer():
            with lock.write_lock():
                events.append("writer in")

        r = run_in_thread(reader)
        reader_inside.wait(2)
        w = run_in_thread(writer)
        time.sleep(0.1)
        assert events == []  # writer is blocked while the reader holds the lock

        release_reader.set()
        r.join(2)
        w.join(2)
        assert events == ["reader done", "writer in"]

    def test_reader_waits_for_writer(self):
        lock = RWLock()
        events = []
        writer_inside = threading.Event()
        release_writer = threading.Event()

        def writer():
            with lock.write_lock():
                writer_inside.set()
                release_writer.wait(2)
                events.append("writer done")

        def reader():
            with lock.read_lock():
                events.append("reader in")

        w = run_in_thread(writer)
        writer_inside.wait(2)
        r = run_in_thread(reader)
        time.sleep(0.1)
        assert events == []

        release_writer.set()
        w.join(2)
        r.join(2)
        assert events == ["writer done", "reader in"]

    def test_writers_are_mutually_exclusive(self):
        lock = RWLock()
        counter = {"value": 0, "inside": 0, "max_inside": 0}

        def writer():
            for _ in range(200):
                with lock.write_lock():
                    counter["inside"] += 1
                    counter["max_inside"] = max(counter["max_inside"], counter["inside"])
                    value = counter["value"]
                    time.sleep(0)
                    counter["value"] = value + 1
                    counter["inside"] -= 1

        threads = [run_in_thread(writer) for _ in range(4)]
        for t in threads:
            t.join(10)

        assert counter["value"] == 800
        assert counter["max_inside"] == 1
