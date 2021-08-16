# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""The base_parser module provides methods that internalize the worker-consumer
pattern when parsing DICOM files.
"""
import os
import queue
import threading

from collections.abc import Callable
from typing import Optional, Union

from pydicom import dcmread

from pacsanini.parse import DicomTagGroup


def _thread_worker(
    parser: DicomTagGroup,
    worker_queue: queue.Queue,
    consumer_queue: queue.Queue,
    stop_working: threading.Event,
    include_path: bool = True,
):
    while True:
        try:
            file_path = worker_queue.get(True, timeout=1)
            if parser is not None:
                result = parser.parse_dicom(file_path)
            else:
                result = {"dicom": dcmread(file_path, stop_before_pixels=True)}
            if include_path:
                result["dicom_path"] = file_path
            consumer_queue.put(result)
        except queue.Empty:
            if stop_working.is_set():
                break
        except Exception:  # pylint: disable=broad-except
            # Catch all exceptions so that a particular thread worker
            # doesn't fail and leave others with extra work.
            pass


def _thread_consumer(
    consumer_queue: queue.Queue,
    stop_consuming: threading.Event,
    callback: Callable,
    callback_args: tuple = None,
    callback_kwargs: dict = None,
):
    if callback_args is None:
        callback_args = ()
    if callback_kwargs is None:
        callback_kwargs = {}

    while True:
        try:
            result = consumer_queue.get(True, timeout=1)
            callback(result, *callback_args, **callback_kwargs)
        except queue.Empty:
            if stop_consuming.is_set():
                break
        except Exception:  # pylint: disable=broad-except
            pass


def _enqueue_files(src: Union[str, os.PathLike], worker_queue: queue.Queue):
    """Enqueue DICOM files into the worker queue."""
    if os.path.isfile(src):
        worker_queue.put(src)
        return

    for root, _, files in os.walk(src):
        for fname in files:
            path = os.path.join(root, fname)
            worker_queue.put(path)


def parse_dir(
    src: Union[str, os.PathLike],
    parser: Optional[DicomTagGroup],
    callback: Callable,
    callback_args: tuple = None,
    callback_kwargs: dict = None,
    nb_threads: int = 1,
    include_path: bool = True,
):
    """Parse a DICOM directory and return the passed results into the
    provided callback function.

    The callback function is responsible for consuming the results of
    the parsed DICOM files.

    Parameters
    ----------
    src : Union[str, os.PathLike]
        The source DICOM path or directory to parse recursively.
    parser : Optional[DicomTagGroup]
        The tags to get the DICOM tag values from. If this is None,
        the results passed to the callback function will not be a dict
        containing a "dicom" key whose value will be the corresponding
        pydicom.Dataset object.
    callback : Callable
        The callback functions to send results to for consumption.
        The first argument of the function should be reserved for
        the parsing result.
    callback_args : tuple
        Extra positional arguments to pass to the callback function.
    callback_kwargs : dict
        Extra keyword arguments to pass to the callback function.
    nb_threads : int
        The number of threads to use for the parsing of DICOM files.
    include_path : bool
        If True, add a "dicom_path" key to the results dict.
    """
    if not os.path.exists(src):
        raise FileNotFoundError(f"'{src}' does not exist.")

    if nb_threads < 1:
        raise ValueError("nb_threads must be greater than 0")

    if not callable(callback):
        raise ValueError("callback must be a callable.")

    try:
        stop_working = threading.Event()
        stop_consuming = threading.Event()

        worker_queue: queue.Queue = queue.Queue()
        consumer_queue: queue.Queue = queue.Queue()

        consumer_thread = threading.Thread(
            target=_thread_consumer,
            args=(consumer_queue, stop_consuming, callback),
            kwargs={"callback_args": callback_args, "callback_kwargs": callback_kwargs},
            daemon=True,
        )
        consumer_thread.start()

        threads = []
        for _ in range(nb_threads):
            thread = threading.Thread(
                target=_thread_worker,
                args=(parser, worker_queue, consumer_queue, stop_working),
                kwargs={"include_path": include_path},
                daemon=True,
            )
            threads.append(thread)
            thread.start()

        _enqueue_files(src, worker_queue)
    finally:
        stop_working.set()
        for worker in threads:
            worker.join()

        stop_consuming.set()
        consumer_thread.join()
