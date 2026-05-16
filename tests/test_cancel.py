#!/usr/bin/env python3
"""Tests for cancel mechanism — threading.Event + progress_hook"""
import threading
import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.downloader import YouTubeDownloader


class TestCancelMechanism(unittest.TestCase):

    def test_cancel_event_initialized_as_threading_event(self):
        d = YouTubeDownloader()
        self.assertIsInstance(d._cancel_event, threading.Event)
        self.assertFalse(d._cancel_event.is_set())

    def test_cancel_download_sets_event(self):
        d = YouTubeDownloader()
        d.cancel_download()
        self.assertTrue(d._cancel_event.is_set())

    def test_progress_hook_raises_when_event_is_set(self):
        d = YouTubeDownloader()
        d._cancel_event.set()
        with self.assertRaises(Exception) as ctx:
            d._progress_hook(
                {'status': 'downloading', 'downloaded_bytes': 500, 'total_bytes': 1000},
                callback=None
            )
        msg = str(ctx.exception).lower()
        self.assertTrue('anulowane' in msg or 'cancelled' in msg or 'canceled' in msg)

    def test_progress_hook_does_not_raise_when_event_not_set(self):
        d = YouTubeDownloader()
        # Should not raise
        d._progress_hook(
            {'status': 'downloading', 'downloaded_bytes': 500, 'total_bytes': 1000},
            callback=None
        )

    def test_cancel_event_cleared_after_reset(self):
        d = YouTubeDownloader()
        d._cancel_event.set()
        d._cancel_event.clear()
        self.assertFalse(d._cancel_event.is_set())


if __name__ == '__main__':
    unittest.main()
