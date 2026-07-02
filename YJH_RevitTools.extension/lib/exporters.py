# -*- coding: utf-8 -*-

from System import Environment
from System.IO import Directory, Path, StreamWriter
from System.Text import UTF8Encoding

from collectors import is_empty, to_text
from grouping import get_issue_group_fields


def csv_escape(value):
    text = to_text(value)

    if u"," in text or u'"' in text or u"\n" in text or u"\r" in text:
        text = text.replace(u'"', u'""')
        return u'"{0}"'.format(text)

    return text


def ensure_folder(folder_path):
    if is_empty(folder_path):
        return False

    if not Directory.Exists(folder_path):
        Directory.CreateDirectory(folder_path)

    return Directory.Exists(folder_path)


def get_save_folder():
    desktop_error = u""
    documents_error = u""

    try:
        desktop_path = Environment.GetFolderPath(
            Environment.SpecialFolder.DesktopDirectory
        )

        if ensure_folder(desktop_path):
            return desktop_path
    except Exception as ex:
        desktop_error = to_text(ex)

    try:
        documents_path = Environment.GetFolderPath(
            Environment.SpecialFolder.MyDocuments
        )

        if ensure_folder(documents_path):
            return documents_path
    except Exception as ex:
        documents_error = to_text(ex)

    raise Exception(
        u"Desktop 및 Documents 폴더를 사용할 수 없습니다. "
        u"Desktop 오류: {0} / Documents 오류: {1}".format(
            desktop_error,
            documents_error
        )
    )


def write_csv_row(writer, values):
    writer.WriteLine(u",".join([csv_escape(value) for value in values]))


def write_csv_metadata(writer, version, summary_data, qc_status):
    write_csv_row(writer, [u"Report Version", version])
    write_csv_row(writer, [u"QC Status", qc_status])
    write_csv_row(writer, [u"Checked Sheets", summary_data["checked_sheets"]])
    write_csv_row(writer, [u"Checked Views", summary_data["checked_views"]])
    write_csv_row(writer, [u"Sheet Issues", summary_data["sheet_issues"]])
    write_csv_row(writer, [u"View Issues", summary_data["view_issues"]])
    write_csv_row(writer, [u"Parameter Issues", summary_data["parameter_issues"]])
    write_csv_row(writer, [u"Total Issues", summary_data["total_issues"]])
    write_csv_row(writer, [u"High", summary_data["high_count"]])
    write_csv_row(writer, [u"Medium", summary_data["medium_count"]])
    write_csv_row(writer, [u"Low", summary_data["low_count"]])
    writer.WriteLine(u"")


def save_full_csv(
    issue_rows,
    summary_data,
    qc_status,
    timestamp,
    version,
    file_prefix
):
    csv_path = Path.Combine(
        get_save_folder(),
        u"{0}_Full_{1}.csv".format(file_prefix, timestamp)
    )
    writer = None

    try:
        writer = StreamWriter(csv_path, False, UTF8Encoding(True))
        write_csv_metadata(writer, version, summary_data, qc_status)
        write_csv_row(
            writer,
            [
                u"Category",
                u"Item Type / Number",
                u"Item Name",
                u"Severity",
                u"QC Item",
                u"Issue Message",
                u"Original Issue Detail"
            ]
        )

        for row in issue_rows:
            qc_item, issue_message = get_issue_group_fields(row)
            write_csv_row(
                writer,
                [row[0], row[1], row[2], row[3], qc_item, issue_message, row[4]]
            )
    finally:
        if writer is not None:
            writer.Close()

    return csv_path


def save_summary_csv(
    group_rows,
    summary_data,
    qc_status,
    timestamp,
    version,
    file_prefix
):
    csv_path = Path.Combine(
        get_save_folder(),
        u"{0}_Summary_{1}.csv".format(file_prefix, timestamp)
    )
    writer = None

    try:
        writer = StreamWriter(csv_path, False, UTF8Encoding(True))
        write_csv_metadata(writer, version, summary_data, qc_status)
        write_csv_row(
            writer,
            [u"Category", u"Item Type", u"QC Item", u"Severity", u"Count", u"Sample Items"]
        )

        for row in group_rows:
            write_csv_row(writer, row)
    finally:
        if writer is not None:
            writer.Close()

    return csv_path
