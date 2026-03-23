from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('register/',views.RegisterView.as_view(),name='register'),
    path('login/',views.LoginView.as_view(),name='login'),
    path('logout/',views.LogoutView.as_view(),name='logout'),
    path('token/refresh/', views.TokenRefreshView.as_view(),name='token-refresh'),
    path('password/forgot/', views.ForgotPasswordView.as_view(),name='password-forgot'),
    path('password/reset/', views.ResetPasswordView.as_view(),name='password-reset'),
    path('password/change/', views.ChangePasswordView.as_view(),name='password-change'),

    # Users
    path('', views.UserListView.as_view(),name='user-list'),
    path('profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('<int:pk>/role/', views.ChangeRoleView.as_view(), name='user-role'),
    path('<int:pk>/', views.UserDetailView.as_view(),  name='user-detail'),

    # Subscriptions
    path('subscriptions/',views.MySubscriptionsView.as_view(),name='my-subscriptions'),
    path('<int:author_id>/subscriptions/',views.AuthorSubscribersView.as_view(), name='author-subscribers'),
    path('<int:author_id>/subscribe/',views.SubscribeView.as_view(), name='subscribe'),
]