from django.urls import path
from . import views

urlpatterns = [
    # Topics
    path('topics/',views.TopicListCreateView.as_view(), name='topic-list'),
    path('topics/<int:pk>/', views.TopicDetailView.as_view(),name='topic-detail'),

    # Blogs
    path('blogs/',views.BlogListCreateView.as_view(),name='blog-list'),
    path('blogs/slug/<slug:slug>/',views.BlogDetailBySlugView.as_view(),name='blog-by-slug'),
    path('blogs/<int:pk>/publish/', views.BlogPublishToggleView.as_view(),name='blog-publish'),
    path('blogs/<int:pk>/', views.BlogDetailByIdView.as_view(),name='blog-detail'),
    path('blogs/author/<int:pk>/',views.BlogsByAuthorView.as_view(),name='blogs-by-author'),

    # Comments
    path('blogs/<int:blog_id>/comments/', views.CommentListCreateView.as_view(), name='comment-list'),
    path('blogs/<int:blog_id>/comments/<int:comment_id>/', views.CommentDetailView.as_view(),name='comment-detail'),
]