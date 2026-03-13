from django.urls import path
from . import views

urlpatterns = [
    path('api/topics/',views.TopicListCreateView.as_view(), name='topic-list-create'),
    path('api/topics/<int:pk>/',views.TopicDetailView.as_view(),name='topic-detail'),
    path('api/blogs/',views.BlogListCreateView.as_view(),name='blog-list-create'),
    path('api/blogs/slug/<slug:slug>/',views.BlogDetailBySlugView.as_view(), name='blog-by-slug'),
    path('api/blogs/<int:pk>/',views.BlogDetailByIdView.as_view(),name='blog-detail'),
    path('api/blogs/<int:pk>/publish/',views.BlogPublishToggleView.as_view(), name='blog-publish'),
    path('api/users/<int:pk>/blogs/',views.BlogsByAuthorView.as_view(),name='user-blogs'),
    path('api/blogs/<int:blog_id>/comments/',views.CommentListCreateView.as_view(),name='comment-list-create'),
    path('api/blogs/<int:blog_id>/comments/<int:comment_id>/',views.CommentDetailView.as_view(),name='comment-detail'),
]