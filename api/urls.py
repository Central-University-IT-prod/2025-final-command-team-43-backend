from drf_spectacular.utils import extend_schema_view, extend_schema
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from django.urls import path

from api import views

urlpatterns = [
    path('ping', views.ping.PingView.as_view()),

    path("token",
         extend_schema_view(post=extend_schema(summary="Authorize user"))(
             TokenObtainPairView
         ).as_view()),
    path("token/refresh",
         extend_schema_view(post=extend_schema(summary="Refresh tokens pair"))(
             TokenRefreshView
         ).as_view()),

    # Auth & Profile
    path('register', views.users.CreateUserView.as_view(role='participant')),
    path('profile', views.users.ProfileView.as_view()),
    path('profile/upload-profile-pic',
         views.users.UploadProfilePicView.as_view()),
    path('users', views.users.ListUserView.as_view()),

    # Teams
    path('teams/<str:pk>/add-members',
         views.teams.TeamMemberActionView.as_view(action='add')),
    path('teams/<str:pk>/remove-members',
         views.teams.TeamMemberActionView.as_view(action='remove')),
    path('teams/<str:pk>', views.teams.TeamView.as_view()),
    path('teams', views.teams.ListCreateTeamView.as_view()),

    # Files
    path('contests/<str:contest_pk>/tasks/<str:pk>/upload-org-files',
         views.tasks.UploadTaskFiles.as_view(files_for='orgs')),
    path('contests/<str:contest_pk>/tasks/<str:pk>/upload-user-files',
         views.tasks.UploadTaskFiles.as_view(files_for='users')),
    path('files/user/<int:pk>/delete',
         views.tasks.DeleteUserFileView.as_view()),
    path('files/org/<int:pk>/delete',
         views.tasks.DeleteOrgFileView.as_view()),

    # Tasks
    path('contests/<str:contest_pk>/tasks/<str:pk>',
         views.tasks.TaskView.as_view()),
    path('contests/<str:contest_pk>/tasks',
         views.tasks.ListCreateTaskView.as_view()),

    # Contests
    path('contests/create', views.contests.CreateContestView.as_view()),
    path('contests/<str:pk>/add-organisers',
         views.contests.ManageOrganisersView.as_view(action="add")),
    path('contests/<str:pk>/remove-organisers',
         views.contests.ManageOrganisersView.as_view(action="remove")),
    path('contests/<str:pk>', views.contests.ContestView.as_view()),
    path('contests', views.contests.ContestListView.as_view()),

    # Solutions
    path('contests/<str:contest_id>/tasks/<str:task_id>/solution',
         views.solutions.PostSolutionAPIView.as_view()),
    path('contests/<str:contest_id>/open-solutions',
         views.solutions.ListOpenSolutionsView.as_view()),
    path('teams/<str:team_id>/solutions/<str:solution_id>/open',
         views.solutions.PublishSolutionView.as_view()),
    path('teams/<str:team_id>/solutions/contest/<str:contest_id>',
         views.solutions.ListMySolutionsView.as_view()),
    path('contests/<str:contest_id>/solutions/unchecked',
         views.solutions.ListUncheckedSolutionsView.as_view()),
    path('contests/<str:contest_id>/solutions/all',
         views.solutions.ListAllSolutionsView.as_view()),
    path('solutions/<str:solution_id>',
         views.solutions.GetSolutionView.as_view()),

    # Verdict
    path('solutions/<str:solution_id>/verdict',
         views.solutions.PostVerdictView.as_view()),

    # Contest states
    path('contests/<str:pk>/ready',
         views.contests.MarkContestReadyView.as_view()),
    path('contests/<str:pk>/finish',
         views.contests.EndCheckingView.as_view()),

    # Stats
    path('stats/user/<str:user_id>',
         views.stats.GetUserStatsView.as_view()),
    path('stats/team/<str:team_id>',
         views.stats.GetTeamStatsView.as_view()),
    path('stats/user/<str:user_id>/achievements',
         views.stats.ListUserAchievementsView.as_view()),
    path('stats/team/<str:team_id>/achievements',
         views.stats.ListTeamAchievementsView.as_view()),
    path('contests/<str:contest_id>/standings',
         views.stats.GetStandings.as_view()),

    # Swagger
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('schema/swagger-ui/',
         SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
