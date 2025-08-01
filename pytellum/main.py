from datetime import datetime

from base import IntellimConn
from config import settings
from cyclopts import App
from rich import print
from rich.console import Console
from rich.table import Table
from utils import console_logger, iso_to_human

logger = console_logger("intellim", level="WARNING")
app = App()

con = IntellimConn(
    settings.get("API_UID"),
    settings.get("PRIVATE_KEY_FILE"),
    settings.get("AUTH_URL"),
    settings.get("BASE_URL"),
    logger=logger,
)


@app.command()
def get_courses(course_name="crew", json=False):
    """Get courses from Intellim."""
    print(f"Getting courses with name: {course_name}")
    if course_name is None:
        params = {}

    params = {"name": course_name}
    courses = con.command("/api/v3/courses", "GET", params=params)

    table = Table(title="\nCourses")

    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="magenta")
    table.add_column("Description", style="green")  # summary
    table.add_column("Catalog", style="blue")
    table.add_column("featured", style="yellow")
    table.add_column("Invite Email", style="red")
    table.add_column("Letters", style="white")

    for course in courses.courses:
        table.add_row(
            str(course.id),
            course.name,
            "",
            course.in_catalog if hasattr(course, "catalog") else "N/A",
            str(course.is_featured),
            str(course.invitation_email),
            str(len(course.letter_triggers)) if hasattr(course, "letter_triggers") else "0",
        )

    console = Console()
    console.print(table)

    return courses.courses


@app.command()
def show_course_sessions(course_id, params=None):
    """Get course sessions for a specific course ID."""
    params = {
        "course_id": course_id,
    }
    sessions = con.command("/api/v3/course_sessions", "GET", params=params).course_sessions

    # print(sessions)
    print(f"{len(sessions)} sessions found for course ID {course_id} - {sessions[0].name}.")

    table = Table(title=f"\nSessions for Course ID {course_id}")
    table.add_column("Session ID", style="cyan", no_wrap=True)
    table.add_column("Course ID", style="blue", no_wrap=True)
    table.add_column("Name", style="magenta")
    table.add_column("status", style="green")
    table.add_column("Letters")
    table.add_column("Start Date (PST)", style="blue")
    table.add_column("End Date (PST)", style="yellow")
    table.add_column("Active", style="red")
    table.add_column("Enrollment", style="white")
    table.add_column("Teams", style="red")
    for session in sessions:
        table.add_row(
            str(session.id),
            str(session.course.id),
            session.name,
            session.status if hasattr(session, "status") else "N/A",
            str(len(session.letter_triggers)),
            iso_to_human(session.start_on, "short", "US/Pacific"),
            iso_to_human(session.end_on, "short", "US/Pacific"),
            str(session.is_active),
            f"0/{str(session.attendance_max)}",
            f"Yes - {session.events[0].id}" if hasattr(session.events[0], "location_type") else "No",
        )

    console = Console()
    console.print(table)


@app.command()
def get_enrollments(course_id, json=False):
    """Get enrollments for a specific course ID."""
    params = {
        "course_id": course_id,
    }
    enrollments = con.command("/api/v3/enrollments", "GET", params=params).__dict__

    # print(enrollments.keys())
    enl = []
    sessionlist = []
    slist = {}
    # Create a dict of enrollments by course_sesson.id
    for enrollment in enrollments["enrollments"]:
        session_id = enrollment.course_session.id
        sessionlist.append(session_id)
        enrollment.__dict__["course_session_id"] = session_id
        enl.append(enrollment.__dict__)
        slist[session_id] = slist.get(session_id, [])
        slist[session_id].append(enrollment)

    for each, value in slist.items():
        # print(f"\n\nSession ID: {each}, Enrollments: {len(slist[each])}")

        table = Table(title=f"\nEnrollments for Session ID {each}")
        table.add_column("Enrollment ID", style="cyan", no_wrap=True)
        table.add_column("User", width=30, no_wrap=True, style="bright_magenta")
        table.add_column("Accepted Invite", style="green")
        table.add_column("Enrolled On", style="yellow")
        table.add_column("Status", style="red")
        table.add_column("Type", style="blue")

        for enrollee in value:
            if enrollee.relationship_type != "instructor":
                (
                    table.add_row(
                        str(enrollee.id),
                        enrollee.created_by,
                        str(enrollee.accepted_invite),
                        iso_to_human(enrollee.enrolled_on, "short", "US/Pacific"),
                        f"{enrollee.status} - {enrollee.progress}",
                        enrollee.relationship_type,
                    ),
                )

        console = Console()
        console.print(table)
    # for enrollment in enrollments['enrollments']:
    #     sessionlist.append(enrollment.course_session.id)
    #     enrollment.__dict__['course_session_id'] = enrollment.course_session.id
    #     enl.append(enrollment.__dict__)
    #     slist[enrollment.course_session.id] = slist.get(enrollment.course_session.id, [])

    # print(enl)
    # print(set(sessionlist))
    # print(enrollments[0])
    # sessionlist = []
    # sessionlist.extend(enrollment.course_session.id for enrollment in enrollments)

    # bysession = []
    # for enrollment in enrollments:
    #     bysession[enrollment.course_session.id].append(enrollment)

    # print(bysession)

    # print(bysession.get(535377))
    # for session in bysession:
    #     # print(f"Session ID: {session_id}, Enrollment ID: {enrollment.id}, User: {enrollment.user.id},
    #  Status: {enrollment.status}")
    #     print(session.keys())
    # table = Table(title=f"\nEnrollments for Course ID {course_id}")
    # table.add_column("Enrollment ID", style="cyan", no_wrap=True)
    # table.add_column("Session", style="blue", no_wrap=True)
    # table.add_column("User ID", style="blue", no_wrap=True)
    # table.add_column("User ", style="magenta")
    # table.add_column("Accepted Invite", style="green")
    # table.add_column("Enrolled_on", style="yellow")
    # table.add_column("Status", style="red")
    # table.add_column("Created At (PST)", style="red")

    # for enrollment in enrollments:
    #     if enrollment.relationship_type != "instructor":
    #         table.add_row(
    #             str(enrollment.id),
    #             str(enrollment.course_session.id),
    #             str(enrollment.user.id),
    #             enrollment.created_by,
    #             str(enrollment.accepted_invite),
    #             enrollment.enrolled_on,
    #             f"{enrollment.status} - {enrollment.progress}",
    #             iso_to_human(enrollment.created_on, "short", "US/Pacific")
    #         )

    # console = Console()
    # console.print(table)


@app.command()
def get_tokens():
    """Get access token from Intellim."""
    con.request_token()
    print(f"Access Token: {con.access_token}")
    print(
        f"Expires At: {con.expires_at} - {datetime.fromtimestamp(con.expires_at)} {datetime.now().astimezone().tzinfo}"
    )


def main():
    app()


if __name__ == "__main__":
    app()
