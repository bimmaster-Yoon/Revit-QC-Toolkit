# -*- coding: utf-8 -*-

import io
import os

from System.Diagnostics import Process, ProcessStartInfo


LATEST_REPORT_FILE = "latest_report_path.txt"


def get_latest_report_pointer(reports_dir):
    return os.path.join(reports_dir, LATEST_REPORT_FILE)


def write_latest_report_path(reports_dir, report_path):
    """마지막 Summary CSV 또는 HTML Report 경로를 UTF-8로 저장한다."""
    if not report_path:
        return u""

    if not os.path.isdir(reports_dir):
        os.makedirs(reports_dir)

    pointer_path = get_latest_report_pointer(reports_dir)

    with io.open(pointer_path, "w", encoding="utf-8") as pointer_file:
        pointer_file.write(report_path)

    return pointer_path


def read_latest_report_path(reports_dir):
    pointer_path = get_latest_report_pointer(reports_dir)

    if not os.path.isfile(pointer_path):
        return u"", u"마지막 리포트 기록이 없습니다. 먼저 Full QC 또는 Quick QC를 실행하세요."

    with io.open(pointer_path, "r", encoding="utf-8-sig") as pointer_file:
        report_path = pointer_file.read().strip()

    if not report_path:
        return u"", u"마지막 리포트 경로가 비어 있습니다."

    if not os.path.isfile(report_path):
        return u"", u"저장된 리포트 파일을 찾을 수 없습니다: {0}".format(
            report_path
        )

    return report_path, u""


def open_file(file_path):
    """Windows 기본 연결 프로그램으로 파일을 연다."""
    if not file_path or not os.path.isfile(file_path):
        return False, u"파일을 찾을 수 없습니다: {0}".format(file_path)

    try:
        start_info = ProcessStartInfo()
        start_info.FileName = file_path
        start_info.UseShellExecute = True
        Process.Start(start_info)
        return True, u""
    except Exception as ex:
        return False, u"파일을 열 수 없습니다: {0}".format(ex)
