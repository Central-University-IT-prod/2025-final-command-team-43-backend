from collections import defaultdict
from datetime import datetime

from django.shortcuts import get_object_or_404

from api import models


def get_total_team_metrics(team_id):
    return (
        models.Solution.objects.filter(author__id=team_id).count(),
        models.Solution.objects.filter(author__id=team_id, is_successful=True).count(),
    )


def get_total_user_metrics(user_id):
    user = get_object_or_404(models.User.objects.all(), id=user_id)
    return (
        models.Solution.objects.filter(author__in=user.teams.all()).count(),
        models.Solution.objects.filter(
            author__in=user.teams.all(), is_successful=True
        ).count(),
    )


def get_activity_graph(user_id):
    user = get_object_or_404(models.User.objects.all(), id=user_id)
    solutions = models.Solution.objects.filter(author__in=user.teams.all())
    graph = defaultdict(int)
    for solution in solutions:
        dt: datetime = solution.created_at
        graph[dt.strftime("%Y-%m-%d")] += 1
    return graph


def get_last_solutions_for_task(contest_id, task_id):
    q = models.Solution.objects.filter(
        task__contest__id=contest_id,
        task__id=task_id
    )
    q = q.order_by("-created_at")
    used = set()
    s = []
    for sol in q:
        if sol.author.id not in used:
            s.append(sol)
            used.add(sol.author.id)
    return s


def get_last_solutions(contest_id):
    contest = get_object_or_404(
        models.Contest.objects.all(), id=contest_id
    )
    s = []
    for task in contest.tasks.all():
        s.extend(get_last_solutions_for_task(contest_id, task.id))
    return s


def _get_last_solutions(contest_id):
    q = models.Solution.objects.filter(task__contest__id=contest_id)
    q = q.order_by("-created_at")
    ids = set()
    used = set()
    for solution in q:
        distinct = f"{solution.author.id}{solution.task.id}"
        if distinct in used:
            continue
        ids.add(solution.id)
        used.add(distinct)
    raise ValueError(f"{ids}")
    return models.Solution.objects.filter(id__in=ids)


def get_standings(contest_id):
    ls = get_last_solutions(contest_id)
    score = {}
    for sol in ls:
        if sol.author.id not in score:
            score[str(sol.author.id)] = 0
        score[str(sol.author.id)] += sol.points
    return score


def get_unchecked_tasks(contest_id):
    contest = get_object_or_404(
        models.Contest.objects.all(), id=contest_id
    )
    ls = get_last_solutions(contest_id)
    s = []
    for sol in ls:
        vd = models.OrgVerdict.objects.filter(solution=sol)
        if vd.count() < contest.cross_check_org_count:
            s.append(sol)
    return s


def _get_standings(contest_id):
    q = models.Solution.objects.all().order_by("-created_at")
    q = q.filter(task__contest__id=contest_id)
    s = defaultdict(int)
    pts = defaultdict(list)
    used = set()
    ids = set()
    points = {}
    for sol in q:
        distinct = f"{sol.task.id}{sol.author.id}"
        if distinct in used:
            continue
        used.add(distinct)
        ids.add(sol.id)
        pts[str(sol.author.id)].append(sol.points)
        s[str(sol.author.id)] += sol.points
        points[str(sol.id)] = sol.points
    return s
