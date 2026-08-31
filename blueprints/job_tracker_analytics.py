from datetime import datetime, timedelta


JOB_STAGES = (
    ("Not Applied Yet", "Saved"),
    ("Applied", "Applied"),
    ("Assessment", "Assessment"),
    ("Interview", "Interview"),
    ("Offer", "Offer"),
    ("Got Job", "Got job"),
    ("Rejected", "Rejected"),
    ("Missed Deadline", "Missed deadline"),
)
JOB_STAGE_VALUES = {value for value, _label in JOB_STAGES}
JOB_INTERVIEW_STAGES = {"Interview", "Offer", "Got Job"}
JOB_ACTIVE_STAGES = {"Applied", "Assessment", "Interview", "Offer"}
JOB_UNSUBMITTED_STAGES = {"Not Applied Yet", "Missed Deadline"}


def parse_job_datetime(value, end_of_day=False):
    value = (value or "").strip().replace(" ", "T")
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if end_of_day and "T" not in value:
        return parsed.replace(hour=23, minute=59, second=59)
    return parsed


def normalise_job_datetime(value):
    value = (value or "").strip()
    if not value:
        return None
    for date_format in ("%d/%m/%Y %H:%M", "%d/%m/%Y"):
        try:
            parsed = datetime.strptime(value, date_format)
            return parsed.isoformat(timespec="minutes") if "%H" in date_format else parsed.date().isoformat()
        except ValueError:
            continue

    candidate = value.replace(" ", "T")
    try:
        datetime.fromisoformat(candidate)
    except ValueError:
        return None
    return candidate


def company_key(company_name):
    return " ".join((company_name or "").casefold().split())


def _elapsed_days(start, end):
    if not start or not end or end < start:
        return None
    return (end - start).total_seconds() / 86400


def _average(values):
    return round(sum(values) / len(values), 1) if values else None


def _application_dates(application):
    return {
        "applied": parse_job_datetime(application.applied_date),
        "assessment": parse_job_datetime(application.assessment_date),
        "interview": parse_job_datetime(application.interview_date),
        "stage_updated": parse_job_datetime(application.stage_updated_at),
    }


def _history_waits(application):
    event_dates = [
        event_date
        for event in application.status_events
        if (event_date := parse_job_datetime(event.changed_at))
    ]
    return [
        wait
        for previous_event, current_event in zip(event_dates, event_dates[1:])
        if (wait := _elapsed_days(previous_event, current_event)) is not None
    ]


def _first_response_wait(application, dates):
    applied_at = dates["applied"]
    if not applied_at:
        return None
    response_dates = [
        response_date
        for response_date in (dates["assessment"], dates["interview"])
        if response_date and response_date >= applied_at
    ]
    stage_updated_at = dates["stage_updated"]
    if application.stage != "Applied" and stage_updated_at and stage_updated_at >= applied_at:
        response_dates.append(stage_updated_at)
    return _elapsed_days(applied_at, min(response_dates)) if response_dates else None


def _company_bucket(application, groups):
    key = company_key(application.company)
    return groups.setdefault(
        key,
        {
            "company": application.company,
            "applications": 0,
            "interviews": 0,
            "assessments": 0,
            "offers": 0,
            "rejections": 0,
            "latest_stage": application.stage,
            "application_ids": [],
            "response_waits": [],
            "jobs": [],
        },
    )


def _update_company_bucket(company, application, dates, response_wait, now):
    company["applications"] += 1
    company["interviews"] += bool(
        application.reached_interview or application.stage in JOB_INTERVIEW_STAGES
    )
    company["assessments"] += bool(
        application.reached_assessment or application.stage == "Assessment"
    )
    company["offers"] += application.stage in {"Offer", "Got Job"}
    company["rejections"] += application.stage == "Rejected"
    company["application_ids"].append(application.id)
    if response_wait is not None:
        company["response_waits"].append(response_wait)

    current_wait = (
        _elapsed_days(dates["applied"], now)
        if application.stage in JOB_ACTIVE_STAGES
        else None
    )
    displayed_wait = response_wait if response_wait is not None else current_wait
    company["jobs"].append(
        {
            "id": application.id,
            "role": application.role,
            "stage": application.stage,
            "applied_date": application.applied_date,
            "location": application.location,
            "work_arrangement": application.work_arrangement,
            "wait_days": round(displayed_wait, 1) if displayed_wait is not None else None,
            "wait_label": "Response" if response_wait is not None else "Waiting",
        }
    )


def _finalise_companies(company_groups):
    company_counts_by_id = {}
    company_stats = []
    for company in company_groups.values():
        application_count = company["applications"]
        company["interview_rate"] = round(
            (company["interviews"] / application_count) * 100
        )
        company["rejection_rate"] = round(
            (company["rejections"] / application_count) * 100
        )
        company["average_wait"] = _average(company.pop("response_waits"))
        company["waiting"] = sum(job["stage"] in JOB_ACTIVE_STAGES for job in company["jobs"])
        company["search_text"] = " ".join(
            [company["company"], *(job["role"] for job in company["jobs"])]
        ).casefold()
        for application_id in company.pop("application_ids"):
            company_counts_by_id[application_id] = application_count
        company_stats.append(company)
    company_stats.sort(key=lambda item: (-item["applications"], item["company"].casefold()))
    return company_stats, company_counts_by_id


def _source_stats(submitted):
    groups = {}
    for application in submitted:
        source_name = application.source.strip() or "Not recorded"
        source = groups.setdefault(
            source_name.casefold(),
            {"source": source_name, "applications": 0, "interviews": 0, "offers": 0},
        )
        source["applications"] += 1
        source["interviews"] += bool(
            application.reached_interview or application.stage in JOB_INTERVIEW_STAGES
        )
        source["offers"] += application.stage in {"Offer", "Got Job"}

    stats = []
    for source in groups.values():
        source["interview_rate"] = round(
            (source["interviews"] / source["applications"]) * 100
        )
        stats.append(source)
    return sorted(stats, key=lambda item: (-item["applications"], item["source"].casefold()))


def _weekly_activity(submitted, now):
    current_week = (now - timedelta(days=now.weekday())).date()
    activity = []
    for week_offset in range(7, -1, -1):
        week_start = current_week - timedelta(weeks=week_offset)
        week_end = week_start + timedelta(days=7)
        count = sum(
            bool(
                (applied_at := parse_job_datetime(application.applied_date))
                and week_start <= applied_at.date() < week_end
            )
            for application in submitted
        )
        activity.append({"label": week_start.strftime("%d %b"), "count": count})
    return activity


def _month_start(value):
    return value.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _shift_month(value, offset):
    month_index = value.year * 12 + value.month - 1 + offset
    return value.replace(year=month_index // 12, month=month_index % 12 + 1, day=1)


def _monthly_activity(submitted, now):
    current_month = _month_start(now)
    months = []
    by_key = {}
    for month_offset in range(-5, 1):
        month = _shift_month(current_month, month_offset)
        item = {
            "key": month.strftime("%Y-%m"),
            "label": month.strftime("%b"),
            "year": month.strftime("%Y"),
            "applications": 0,
            "assessments": 0,
            "interviews": 0,
            "outcomes": 0,
        }
        months.append(item)
        by_key[item["key"]] = item

    for application in submitted:
        dates = _application_dates(application)
        dated_metrics = (
            (dates["applied"], "applications"),
            (dates["assessment"], "assessments"),
            (dates["interview"], "interviews"),
        )
        for event_date, metric in dated_metrics:
            if event_date and (month := by_key.get(event_date.strftime("%Y-%m"))):
                month[metric] += 1

        if application.stage in {"Rejected", "Offer", "Got Job"}:
            outcome_date = dates["stage_updated"]
            if outcome_date and (month := by_key.get(outcome_date.strftime("%Y-%m"))):
                month["outcomes"] += 1

    for month in months:
        month["total_activity"] = sum(
            month[key] for key in ("applications", "assessments", "interviews", "outcomes")
        )
    return months


def _application_period_comparison(submitted, now):
    current_start = now - timedelta(days=30)
    previous_start = now - timedelta(days=60)
    current = 0
    previous = 0
    for application in submitted:
        applied_at = parse_job_datetime(application.applied_date)
        if not applied_at:
            continue
        if current_start <= applied_at <= now:
            current += 1
        elif previous_start <= applied_at < current_start:
            previous += 1

    change = current - previous
    return {
        "current": current,
        "previous": previous,
        "change": change,
        "direction": "up" if change > 0 else "down" if change < 0 else "steady",
    }


def _rejection_reason_stats(submitted):
    counts = {}
    for application in submitted:
        if application.stage != "Rejected":
            continue
        reason = application.rejection_reason.strip() or "Not recorded"
        counts[reason] = counts.get(reason, 0) + 1

    total = sum(counts.values())
    return [
        {
            "reason": reason,
            "count": count,
            "percentage": round((count / total) * 100) if total else 0,
        }
        for reason, count in sorted(counts.items(), key=lambda item: (-item[1], item[0].casefold()))
    ]


def job_tracker_metrics(applications, now):
    submitted = [app for app in applications if app.stage not in JOB_UNSUBMITTED_STAGES]
    submitted_count = len(submitted)
    interviews = sum(
        bool(app.reached_interview or app.stage in JOB_INTERVIEW_STAGES)
        for app in submitted
    )
    assessments = sum(
        bool(app.reached_assessment or app.stage == "Assessment")
        for app in submitted
    )
    offers = sum(app.stage in {"Offer", "Got Job"} for app in submitted)
    jobs = sum(app.stage == "Got Job" for app in submitted)
    rejections = sum(app.stage == "Rejected" for app in submitted)
    active = sum(app.stage in JOB_ACTIVE_STAGES for app in submitted)

    company_groups = {}
    transition_waits = []
    assessment_waits = []
    interview_waits = []
    assessment_to_interview_waits = []
    rejection_waits = []
    active_waits = []
    recent_applications = 0
    waiting_over_14_days = 0

    for application in submitted:
        dates = _application_dates(application)
        history_waits = _history_waits(application)
        transition_waits.extend(history_waits)
        response_wait = _first_response_wait(application, dates)
        company = _company_bucket(application, company_groups)
        _update_company_bucket(company, application, dates, response_wait, now)

        applied_at = dates["applied"]
        assessment_at = dates["assessment"]
        interview_at = dates["interview"]
        stage_updated_at = dates["stage_updated"]
        if applied_at and applied_at >= now - timedelta(days=30):
            recent_applications += 1

        assessment_wait = _elapsed_days(applied_at, assessment_at)
        if assessment_wait is not None:
            assessment_waits.append(assessment_wait)
            if not history_waits:
                transition_waits.append(assessment_wait)

        interview_wait = _elapsed_days(applied_at, interview_at)
        if interview_wait is not None:
            interview_waits.append(interview_wait)

        interview_transition = _elapsed_days(assessment_at or applied_at, interview_at)
        if interview_transition is not None:
            assessment_to_interview_waits.append(interview_transition)
            if not history_waits:
                transition_waits.append(interview_transition)

        if application.stage == "Rejected":
            rejection_wait = _elapsed_days(applied_at, stage_updated_at)
            if rejection_wait is not None:
                rejection_waits.append(rejection_wait)

        if application.stage in {"Rejected", "Offer", "Got Job"} and not history_waits:
            final_transition = _elapsed_days(
                interview_at or assessment_at or applied_at,
                stage_updated_at,
            )
            if final_transition is not None:
                transition_waits.append(final_transition)

        if application.stage in JOB_ACTIVE_STAGES:
            status_started_at = stage_updated_at
            if not status_started_at and application.stage == "Assessment":
                status_started_at = assessment_at
            if not status_started_at and application.stage == "Interview":
                status_started_at = interview_at
            active_wait = _elapsed_days(status_started_at or applied_at, now)
            if active_wait is not None:
                active_waits.append(active_wait)
            application_age = _elapsed_days(applied_at, now)
            if application.stage == "Applied" and application_age is not None:
                waiting_over_14_days += application_age >= 14

    company_stats, company_counts_by_id = _finalise_companies(company_groups)
    weekly_activity = _weekly_activity(submitted, now)
    monthly_activity = _monthly_activity(submitted, now)
    period_comparison = _application_period_comparison(submitted, now)
    responded = sum(
        app.stage not in {"Applied", "Not Applied Yet"}
        or app.reached_assessment
        or app.reached_interview
        for app in submitted
    )
    reminders_due = sum(
        bool(
            not app.reminder_done
            and (follow_up := parse_job_datetime(app.follow_up_date, end_of_day=True))
            and follow_up.date() <= (now + timedelta(days=7)).date()
        )
        for app in applications
    )

    def rate(count):
        return round((count / submitted_count) * 100) if submitted_count else 0

    return {
        "submitted": submitted_count,
        "interviews": interviews,
        "assessments": assessments,
        "offers": offers,
        "jobs": jobs,
        "rejections": rejections,
        "active": active,
        "companies": len(company_groups),
        "repeat_companies": sum(company["applications"] > 1 for company in company_stats),
        "repeat_applications": submitted_count - len(company_groups),
        "recent_applications": recent_applications,
        "waiting_over_14_days": waiting_over_14_days,
        "reminders_due": reminders_due,
        "interview_rate": rate(interviews),
        "assessment_rate": rate(assessments),
        "offer_rate": rate(offers),
        "rejection_rate": rate(rejections),
        "response_rate": rate(responded),
        "assessment_to_interview_rate": (
            round((interviews / assessments) * 100) if assessments else 0
        ),
        "average_stage_wait": _average(transition_waits),
        "average_assessment_wait": _average(assessment_waits),
        "average_interview_wait": _average(interview_waits),
        "average_assessment_to_interview": _average(assessment_to_interview_waits),
        "average_rejection_wait": _average(rejection_waits),
        "average_active_wait": _average(active_waits),
        "fastest_interview": round(min(interview_waits), 1) if interview_waits else None,
        "longest_active_wait": round(max(active_waits), 1) if active_waits else None,
        "timed_transitions": len(transition_waits),
        "company_stats": company_stats,
        "company_counts_by_id": company_counts_by_id,
        "source_stats": _source_stats(submitted),
        "rejection_reason_stats": _rejection_reason_stats(submitted),
        "weekly_activity": weekly_activity,
        "weekly_max": max((week["count"] for week in weekly_activity), default=0),
        "monthly_activity": monthly_activity,
        "monthly_max": max((month["total_activity"] for month in monthly_activity), default=0),
        "period_comparison": period_comparison,
        "funnel": (
            {"label": "Applied", "count": submitted_count, "rate": 100 if submitted_count else 0},
            {"label": "Assessment", "count": assessments, "rate": rate(assessments)},
            {"label": "Interview", "count": interviews, "rate": rate(interviews)},
            {"label": "Offer", "count": offers, "rate": rate(offers)},
            {"label": "Got job", "count": jobs, "rate": rate(jobs)},
        ),
    }
