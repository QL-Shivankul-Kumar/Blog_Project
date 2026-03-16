from django.urls import path
from . import views

urlpatterns = [
    path('api/auth/register/',views.RegisterView.as_view(),name='auth-register'),
    path('api/auth/login/',views.LoginView.as_view(),name='auth-login'),
    path('api/auth/logout/',views.LogoutView.as_view(),name='auth-logout'),
    path('api/auth/refresh/',views.TokenRefreshView.as_view(),name='auth-refresh'),
    path('api/auth/forgot-password/', views.ForgotPasswordView.as_view(), name='auth-forgot-password'),
    path('api/auth/reset-password',  views.ResetPasswordView.as_view(),  name='auth-reset-password'),
    path('api/auth/change-password/', views.ChangePasswordView.as_view(), name='auth-change-password'),
    path('api/users/',views.UserListView.as_view(),   name='user-list'),
    path('api/users/profile/',views.UserProfileView.as_view(),         name='user-me'),
    path('api/users/<int:pk>/role/',views.ChangeRoleView.as_view(), name='user-change-role'),
    path('api/users/<int:pk>/',views.UserDetailView.as_view(), name='user-detail'),
    path('api/subscriptions/me/',
         views.MySubscriptionsView.as_view(),   name='my-subscriptions'),
    path('api/subscriptions/author/<int:author_id>/',
         views.AuthorSubscribersView.as_view(), name='author-subscribers'),
    path('api/subscriptions/<int:author_id>/',
         views.SubscribeView.as_view(),         name='subscribe'),
]