from enum import IntEnum


class JobStatus(IntEnum):
    VALID = 0
    INVALID = 1
    RUNNING = 2
    COMPLETED = 3
    FAILED = 4
    SUBMITTED = 5
    PENDING = 6
    WAITING_ON_INPUT = 7
    CANCELLED = 8
    TIMEOUT = 9
    OTHER = 10

StatusMap = {
    'VALID': JobStatus.VALID,
    'INVALID': JobStatus.INVALID,
    'RUNNING': JobStatus.RUNNING,
    'COMPLETED': JobStatus.COMPLETED,
    'FAILED': JobStatus.FAILED,
    'SUBMITTED': JobStatus.SUBMITTED,
    'PENDING': JobStatus.PENDING,
    'WAITING_ON_INPUT': JobStatus.WAITING_ON_INPUT,
    'CANCELLED': JobStatus.CANCELLED,
    'COMPLETING': JobStatus.COMPLETED,
    'TIMEOUT': JobStatus.TIMEOUT,
    'OTHER': JobStatus.OTHER
}

ReverseMap = {
    JobStatus.TIMEOUT: "Timeout",
    JobStatus.VALID: "Valid",
    JobStatus.INVALID: "Invalid",
    JobStatus.RUNNING: "Running",
    JobStatus.COMPLETED: "Completed",
    JobStatus.FAILED: "Failed",
    JobStatus.SUBMITTED: "Submitted",
    JobStatus.PENDING: "Pending",
    JobStatus.WAITING_ON_INPUT: "Waiting on additional files",
    JobStatus.CANCELLED: "Canceled",
    JobStatus.OTHER: "Other"
}
