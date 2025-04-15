from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import ArrayField

from os import path
import uuid


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class Team(BaseModel):
    name = models.CharField(max_length=128, blank=False)
    individual = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.name + (" (individual)" if self.individual else "")


class User(AbstractUser):
    class Role(models.TextChoices):
        PARTICIPANT = "participant"
        ORGANISER = "organiser"

    def get_filename(instance, filename):
        ext = path.splitext(filename)[1]
        return "profile_pics/%s%s" % (instance.pk, ext)

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    profile_pic = models.FileField(upload_to=get_filename, null=True)
    role = models.CharField(max_length=32, choices=Role.choices, default=Role.ORGANISER)
    teams = models.ManyToManyField(to=Team, related_name="members")

    def delete(self, *args, **kwargs):
        self.profile_pic.delete()
        return super().delete(*args, **kwargs)


class Contest(BaseModel):
    class Stages(models.TextChoices):
        PREPARING = "preparing"
        IN_PROGRESS = "in_progress"
        CHECKING = "checking"
        FINISHED = "finished"

    title = models.CharField(max_length=256)
    description = models.TextField()
    start_datetime = models.DateTimeField(null=True)
    end_datetime = models.DateTimeField(null=True, db_index=True)
    stage = models.CharField(
        max_length=64, choices=Stages.choices, default=Stages.PREPARING
    )
    cross_check_org_count = models.PositiveIntegerField(default=2)
    organisers = models.ManyToManyField(to=User, related_name="contests")


class Task(BaseModel):
    class AnswerTypes(models.TextChoices):
        TEXT = "text"
        NUMBER = "number"
        FILE = "file"
        CHOICE = "choice"

    contest = models.ForeignKey(
        to=Contest, related_name="tasks", on_delete=models.CASCADE
    )
    title = models.CharField(max_length=256)
    description = models.TextField()
    org_text = models.TextField()
    answer_type = models.CharField(max_length=16, choices=AnswerTypes.choices)
    supported_file_formats = ArrayField(models.CharField(max_length=16), null=True)
    max_attempts = models.PositiveIntegerField(null=True)
    max_points = models.PositiveIntegerField()
    checker = models.JSONField(null=True)
    choices = models.JSONField(null=True)


class Solution(BaseModel):
    def get_filename(instance, filename):
        ext = path.splitext(filename)[1]
        return "solution_files/%s%s" % (uuid.uuid4(), ext)

    task = models.ForeignKey(
        to=Task, related_name="solutions", on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        to=Team, related_name="solutions", on_delete=models.CASCADE
    )
    file = models.FileField(upload_to=get_filename, null=True)
    content = models.TextField(blank=False, null=True)
    points = models.PositiveIntegerField()
    is_successful = models.BooleanField()
    is_public = models.BooleanField()
    is_checked = models.BooleanField(default=False)

    def delete(self, *args, **kwargs):
        self.file.delete()
        return super().delete(*args, **kwargs)


class BaseFileModel(models.Model):
    def get_filename(instance, filename):
        ext = path.splitext(filename)[1]
        return "files/%s%s" % (uuid.uuid4(), ext)

    file = models.FileField(upload_to=get_filename)

    def delete(self, *args, **kwargs):
        self.file.delete()
        return super().delete(*args, **kwargs)

    class Meta:
        abstract = True


class OrgFile(BaseFileModel):
    task = models.ForeignKey(
        to=Task, related_name="org_files", on_delete=models.CASCADE
    )


class UserFile(BaseFileModel):
    task = models.ForeignKey(
        to=Task, related_name="user_files", on_delete=models.CASCADE
    )


class OrgVerdict(BaseModel):
    solution = models.ForeignKey(
        to=Solution,
        related_name="verdicts",
        on_delete=models.CASCADE,
        verbose_name="Решение",
        related_query_name="verdict",
    )
    org = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        verbose_name="Проверяющий организатор",
        related_name="verdicts",
    )
    points = models.PositiveIntegerField(verbose_name="Балл")

    class Meta:
        verbose_name = "Оценка решения"
        verbose_name_plural = "Оценки решений"


class Achievement(BaseModel):
    team = models.ForeignKey(
        to=Team, related_name="achievements", on_delete=models.CASCADE
    )
    contest = models.ForeignKey(to=Contest, on_delete=models.CASCADE)
    place = models.PositiveIntegerField()
