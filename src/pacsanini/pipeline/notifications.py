# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""The notifications module provides variables and methods that are
used by prefect tasks to notify end-users of task states.
"""
import os
import smtplib

from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, cast

from loguru import logger
from prefect import Task, context
from prefect.engine.state import State

from pacsanini import db
from pacsanini.config import PacsaniniConfig
from pacsanini.models import QueryLevel


BASE_TEMPLATE = """\
<html>
    <head></head>
    <body>
    <table align="left" border="0" cellpadding="2px" cellspacing="2px">
        <tr>
            <td style="border-left: 2px solid {color}; padding-left: 6px;">
                {text}
            </td>
        </tr>
    </table>
    </body>
</html>
"""


def format_email_message(
    task: Task, state: State, email_to: str, detail: str = ""
) -> str:
    """Format an email message based on the state of a task."""
    if isinstance(state.result, Exception):
        msg = f"<pre>{repr(state.result)}</pre>"
    else:
        msg = f'"{state.message}"'

    color = state.color
    text = f"""
    <pre>{task.name}</pre>
    is now in a <font color="{state.color}"><b>{type(state).__name__}</b></font> state
    <br><br>
    <b>Message:</b><br>{msg}
    """
    if detail:
        text += f"<br><br><b>Details:</b><br>{detail}"

    contents = MIMEMultipart("alternative")
    contents.attach(MIMEText(text, "plain"))
    contents.attach(MIMEText(BASE_TEMPLATE.format(color=color, text=text), "html"))

    contents["Subject"] = Header(f"Pacsanini state update for {task.name}", "UTF-8")
    contents["From"] = email_to
    contents["To"] = email_to

    return contents.as_string()


def send_mail(config: PacsaniniConfig, msg: str):
    """Send an email using the pacsanini configuration and the specified
    email message. Messages are sent using the gmail server over port 465.
    """
    user_email = config.email.username
    user_password = config.email.password

    server: smtplib.SMTP_SSL = None
    try:
        server = smtplib.SMTP_SSL(config.email.host, config.email.port)
        server.login(user_email, user_password)
        server.sendmail(user_email, user_email, msg)
    except Exception as exc:
        logger.warning(f"Email notification for {user_email} failed due to {exc}")
    finally:
        if server is not None:
            server.quit()


def find_email_notifier(obj: Task, old_state: State, new_state: State) -> State:
    """Send a custom email notification only when the C-FIND task is finished
    (this can be in a state of success or failure).

    Parameters
    ----------
    obj : Task
        The find task.
    old_state : State
        The task's previous state.
    new_state : State
        The task's new state.

    Returns
    -------
    State
        The task's new state.
    """
    if not new_state.is_finished():
        return new_state

    config = cast(PacsaniniConfig, context["pacsanini_config"])
    if not (config.email.username and config.email.password):
        return new_state

    with db.get_db_session(config.storage.resources) as session:
        study_count = len(db.get_study_uids_to_move(session))
    start_date = config.find.start_date.strftime("%Y-%m-%d")
    end_date = config.find.end_date.strftime("%Y-%m-%d")
    detail = f"Studies retrieved between {start_date} and {end_date}: {study_count}"

    msg = format_email_message(obj, new_state, config.email.username, detail=detail)
    send_mail(config, msg)
    return new_state


def move_email_notifier(
    obj: Task, old_state: State, new_state: State
) -> Optional[State]:
    """Send a custom email notification when the C-MOVE task is finished
    (this can be in a state of failure or of success).

    Parameters
    ----------
    obj : Task
        The find task.
    old_state : State
        The task's previous state.
    new_state : State
        The task's new state.

    Returns
    -------
    State
        The task's new state.
    """
    if not new_state.is_finished():
        return new_state

    config = cast(PacsaniniConfig, context["pacsanini_config"])
    if not (config.email.username and config.email.password):
        return new_state

    moved_resources = len([entry for entry in os.scandir(config.storage.directory)])
    detail = "Number of {level} moved: {count}"
    if config.storage.sort_by == QueryLevel.PATIENT:
        detail = detail.format(level="patients", count=moved_resources)
    elif config.storage.sort_by == QueryLevel.STUDY:
        detail = detail.format(level="studies", count=moved_resources)
    else:
        detail = detail.format(level="images", count=moved_resources)

    msg = format_email_message(obj, new_state, config.email.username, detail=detail)
    send_mail(config, msg)
    return new_state
