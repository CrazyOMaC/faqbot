"""Validated types shared by the API, terminal, and storage layer."""

from typing import Final

from pydantic import BaseModel, ConfigDict, Field, field_validator


def normalize_word(value: str) -> str:
    """Keep topic names and keywords consistent with the word matcher."""
    word = value.strip().lower()
    if not word.isascii() or not word.isalpha() or len(word) > 32:
        raise ValueError("Use one word of 1 to 32 English letters.")
    return word


class FAQ(BaseModel):
    """One topic word, its alternative keywords, and its saved answer."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    topic: str = Field(min_length=1, max_length=32)
    keywords: tuple[str, ...] = Field(min_length=1, max_length=20)
    answer: str = Field(min_length=1, max_length=2000)

    @field_validator("topic")
    @classmethod
    def validate_topic(cls, value: str) -> str:
        return normalize_word(value)

    @field_validator("keywords")
    @classmethod
    def validate_keywords(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(dict.fromkeys(normalize_word(word) for word in value))


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    message: str = Field(min_length=1, max_length=2000)


class ChatReply(BaseModel):
    message: str
    matches: tuple[FAQ, ...] = ()
    suggestions: tuple[str, ...] = ()


DEFAULT_FAQS: Final[tuple[FAQ, ...]] = (
    FAQ(
        topic="assignment",
        keywords=("due", "deadline", "submit"),
        answer="Friday, 5 PM.",
    ),
    FAQ(
        topic="notes",
        keywords=("notes",),
        answer="Python folder in the class drive.",
    ),
    FAQ(
        topic="exam",
        keywords=("timetable", "schedule", "when", "date", "time", "room"),
        answer=(
            "Python exam: 14 December 2026, 10 AM-12 PM, Room 204. "
            "Arrive by 9:30 AM with your student ID."
        ),
    ),
    FAQ(
        topic="library",
        keywords=(
            "hours",
            "open",
            "opens",
            "close",
            "closes",
            "closed",
            "timings",
            "books",
            "borrow",
            "return",
            "rules",
            "where",
            "location",
        ),
        answer=(
            "The library is on the ground floor of Block B. "
            "Open Monday-Friday, 9 AM-6 PM, and Saturday, 10 AM-2 PM; "
            "closed on Sundays. You can borrow 3 books for 14 days "
            "using your student ID."
        ),
    ),
    FAQ(
        topic="attendance",
        keywords=(
            "check",
            "percentage",
            "record",
            "requirement",
            "minimum",
            "required",
        ),
        answer=(
            "At least 75% attendance is required in each subject. "
            "Attendance percentage = classes attended / classes held x 100. "
            "Your individual record is under Student Portal > Academics > Attendance."
        ),
    ),
    FAQ(
        topic="syllabus",
        keywords=("find", "download", "get", "where", "python"),
        answer=(
            "The Python syllabus covers fundamentals and control flow; "
            "strings and collections; functions and modules; file handling; "
            "and exceptions and object-oriented programming. "
            "The PDF is in Class Drive > Python > Syllabus.pdf."
        ),
    ),
    FAQ(
        topic="fees",
        keywords=("pay", "payment", "amount", "due", "receipt"),
        answer=(
            "Semester tuition is INR 45,000, due on 15 November 2026. "
            "To pay, open Student Portal > Fees > Pay Now, choose UPI, card, "
            "or net banking, and download the receipt after payment."
        ),
    ),
    FAQ(
        topic="results",
        keywords=("check", "view", "marks", "published", "where", "when"),
        answer=(
            "Semester results will be published on 20 December 2026 at 3 PM. "
            "Open Student Portal > Examinations > Results, select Semester 3, "
            "and download your marksheet."
        ),
    ),
    FAQ(
        topic="scholarship",
        keywords=("apply", "application", "eligibility", "deadline", "documents"),
        answer=(
            "The merit scholarship gives a 25% tuition waiver for a previous "
            "semester score of at least 80%. Apply by 30 November 2026 through "
            "Student Portal > Scholarships. Upload your marksheet, student ID, "
            "and fee receipt."
        ),
    ),
    FAQ(
        topic="registration",
        keywords=("course", "subject", "apply", "register", "help", "deadline"),
        answer=(
            "Course registration closes on 10 November 2026 at 5 PM. "
            "Open Student Portal > Academics > Course Registration, "
            "select your Semester 3 subjects, click Submit, "
            "and download the confirmation slip."
        ),
    ),
    FAQ(
        topic="practical",
        keywords=("lab", "schedule", "files", "requirements", "when"),
        answer=(
            "Python practicals are on Tuesdays, 2-4 PM, in Computer Lab 2. "
            "Bring your student ID, laptop, and practical notebook. "
            "Upload each .py file to Class Drive > Python > Practicals "
            "before the next lab session."
        ),
    ),
    FAQ(
        topic="project",
        keywords=("topic", "group", "submit", "submission", "requirements"),
        answer=(
            "Build an FAQ chatbot in Python in a group of 4-6 students. "
            "Submit the source code, README, and presentation to "
            "Class Drive > Python > Projects by 27 November 2026, 5 PM. "
            "Show question matching, an unknown question, and adding a new FAQ."
        ),
    ),
    FAQ(
        topic="transport",
        keywords=("bus", "route", "schedule", "timing", "stops"),
        answer=(
            "Bus Route 1: Central Station, 7:30 AM; City Square, 7:45 AM; "
            "campus arrival, 8:15 AM. The return bus leaves the campus "
            "main gate at 5:15 PM, Monday-Friday. Carry your bus pass."
        ),
    ),
    FAQ(
        topic="hostel",
        keywords=("apply", "application", "room", "availability", "rules"),
        answer=(
            "Hostel applications are open from 1-15 November 2026 through "
            "Student Portal > Hostel > Apply. Rooms are shared by two students. "
            "Upload a student ID and guardian contact details. "
            "Check-in is 10 AM-4 PM on weekdays; quiet hours are 10 PM-6 AM."
        ),
    ),
    FAQ(
        topic="contact",
        keywords=("teacher", "office", "help", "rep", "department"),
        answer=(
            "Python teacher: Room 204, Monday-Friday, 2-3 PM. "
            "Academic office: Block A, Room 101, Monday-Friday, 10 AM-4 PM. "
            "Bring your student ID and any relevant submission or payment receipt."
        ),
    ),
)
