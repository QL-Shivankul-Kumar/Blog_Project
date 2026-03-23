from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import Topic, Blog, Comment
from .serializers import (
    TopicSerializer,
    BlogListSerializer, BlogDetailSerializer,
    BlogCreateSerializer, BlogUpdateSerializer,
    BlogInTopicSerializer,
    CommentSerializer, CommentUpdateSerializer,
)
from core.permissions import IsAdminUser, IsAuthorOrAdmin
from core.utils.responder import success_response
from core.pagination import BlogPagination
from core.constants.messages import BlogMessages, TopicMessages, CommentMessages
from core.exceptions import (
    AppValidationError, ResourceNotFound,
    CustomPermissionDenied as PermissionDenied, ConflictError,
    UnprocessableEntity, CustomAuthFailed as AuthenticationFailed,
)
from core.utils.email import send_subscriber_emails_async

class TopicListCreateView(APIView):

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated(), IsAuthorOrAdmin()]

    def get(self, request):
        topics = Topic.objects.with_blog_count().order_by('name')
        return success_response(
            data=TopicSerializer(topics, many=True).data,
            message=TopicMessages.LIST_FETCHED,
        )

    def post(self, request):
        serializer = TopicSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        topic = serializer.save(created_by=request.user)
        return success_response(
            data=TopicSerializer(topic).data,
            message=TopicMessages.CREATED,
            status_code=status.HTTP_201_CREATED,
        )


class TopicDetailView(APIView):

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated(), IsAdminUser()]

    def get(self, request, pk):
        try:
            topic = Topic.objects.get_with_blogs(pk)
        except Topic.DoesNotExist:
            raise ResourceNotFound(TopicMessages.NOT_FOUND)

        topic_data = TopicSerializer(topic).data
        topic_data['blogs'] = BlogInTopicSerializer(
            Blog.objects.filter(
                topic=topic, is_published=True
            ).select_related('author'),
            many=True,
        ).data
        return success_response(
            data=topic_data,
            message=TopicMessages.FETCHED,
        )

    def delete(self, request, pk):
        topic = get_object_or_404(Topic, pk=pk)
        try:
            topic.delete()
            return success_response(
                message=TopicMessages.DELETED,
                status_code=status.HTTP_204_NO_CONTENT,
            )
        except Exception:
            raise ConflictError(TopicMessages.DELETE_BLOCKED)

class BlogListCreateView(APIView):

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated(), IsAuthorOrAdmin()]

    def get(self, request):
        queryset = Blog.objects.published().select_related('author', 'topic')
        title    = request.query_params.get('title')
        if title:
            queryset = queryset.filter(title__icontains=title)
        paginator  = BlogPagination()
        page       = paginator.paginate_queryset(queryset, request)
        serializer = BlogListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = BlogCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        extra = {
            'author': request.user,
            'slug':   Blog.objects.generate_unique_slug(
                serializer.validated_data['title']
            ),
        }
        if serializer.validated_data.get('is_published'):
            extra['published_at'] = timezone.now()
        blog = serializer.save(**extra)
        if blog.is_published:
            send_subscriber_emails_async(blog)
        return success_response(
            data=BlogDetailSerializer(blog).data,
            message=BlogMessages.CREATED,
            status_code=status.HTTP_201_CREATED,
        )


class BlogDetailByIdView(APIView):
    permission_classes = [AllowAny]

    def _get_blog(self, pk):
        return get_object_or_404(
            Blog.objects.select_related('author', 'topic'), pk=pk
        )

    def get(self, request, pk):
        blog = self._get_blog(pk)
        if not blog.is_published:
            if not request.user.is_authenticated:
                raise PermissionDenied(BlogMessages.NOT_PUBLISHED)
            if request.user != blog.author and request.user.role != 'admin':
                raise PermissionDenied(BlogMessages.NOT_PUBLISHED)
        if not request.user.is_authenticated or request.user != blog.author:
            blog.increment_view()
        return success_response(
            data=BlogDetailSerializer(blog).data,
            message=BlogMessages.FETCHED,
        )

    def patch(self, request, pk):
        if not request.user.is_authenticated:
            raise AuthenticationFailed(BlogMessages.AUTH_REQUIRED)
        blog = self._get_blog(pk)
        if request.user != blog.author:
            raise PermissionDenied(BlogMessages.EDIT_FORBIDDEN)
        was_draft  = not blog.is_published
        serializer = BlogUpdateSerializer(blog, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        blog = serializer.save()
        if was_draft and blog.is_published:
            if not blog.published_at:
                blog.published_at = timezone.now()
                blog.save(update_fields=['published_at'])
            send_subscriber_emails_async(blog)
        return success_response(
            data=BlogDetailSerializer(blog).data,
            message=BlogMessages.UPDATED,
        )

    def delete(self, request, pk):
        if not request.user.is_authenticated:
            raise AuthenticationFailed(BlogMessages.AUTH_REQUIRED)
        blog = self._get_blog(pk)
        if request.user != blog.author and request.user.role != 'admin':
            raise PermissionDenied(BlogMessages.DEL_FORBIDDEN)
        blog.delete()
        return success_response(
            message=BlogMessages.DELETED,
            status_code=status.HTTP_204_NO_CONTENT,
        )


class BlogDetailBySlugView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug):
        blog = get_object_or_404(
            Blog.objects.select_related('author', 'topic'), slug=slug
        )
        if not blog.is_published:
            if not request.user.is_authenticated:
                raise PermissionDenied(BlogMessages.NOT_PUBLISHED)
            if request.user != blog.author and request.user.role != 'admin':
                raise PermissionDenied(BlogMessages.NOT_PUBLISHED)
        if not request.user.is_authenticated or request.user != blog.author:
            blog.increment_view()
        return success_response(
            data=BlogDetailSerializer(blog).data,
            message=BlogMessages.FETCHED,
        )


class BlogPublishToggleView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        blog = get_object_or_404(Blog, pk=pk)
        if blog.author is None:
            raise UnprocessableEntity(BlogMessages.NO_AUTHOR)
        if request.user != blog.author:
            raise PermissionDenied(BlogMessages.PUB_FORBIDDEN)
        is_published = request.data.get('is_published')
        if is_published is None:
            raise AppValidationError(BlogMessages.IS_PUB_REQUIRED)
        was_draft         = not blog.is_published
        blog.is_published = is_published
        if is_published and not blog.published_at:
            blog.published_at = timezone.now()
        blog.save()
        if was_draft and blog.is_published:
            send_subscriber_emails_async(blog)
        return success_response(
            data=BlogDetailSerializer(blog).data,
            message=BlogMessages.PUBLISHED if blog.is_published else BlogMessages.UNPUBLISHED,
        )


class BlogsByAuthorView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        from apps.users.models import User
        author   = get_object_or_404(User, pk=pk)
        queryset = Blog.objects.published_by_author(author.id)
        if request.user.is_authenticated:
            if request.user.pk == author.pk or request.user.role == 'admin':
                show = request.query_params.get('is_published')
                if show == 'false':
                    queryset = Blog.objects.by_author(author.id).filter(
                        is_published=False
                    )
                elif show is None:
                    queryset = Blog.objects.by_author(author.id)
        paginator  = BlogPagination()
        page       = paginator.paginate_queryset(queryset, request)
        serializer = BlogListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

class CommentListCreateView(APIView):

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    def _get_blog(self, blog_id):
        return get_object_or_404(Blog, pk=blog_id, is_published=True)

    def get(self, request, blog_id):
        blog     = self._get_blog(blog_id)
        comments = Comment.objects.for_blog(blog.id)
        return success_response(
            data=CommentSerializer(comments, many=True).data,
            message=CommentMessages.LIST_FETCHED,
        )

    def post(self, request, blog_id):
        blog       = self._get_blog(blog_id)
        serializer = CommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = serializer.save(blog=blog, user=request.user)
        return success_response(
            data=CommentSerializer(comment).data,
            message=CommentMessages.CREATED,
            status_code=status.HTTP_201_CREATED,
        )


class CommentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_comment(self, blog_id, comment_id):
        return get_object_or_404(
            Comment, pk=comment_id, blog_id=blog_id, is_deleted=False
        )

    def patch(self, request, blog_id, comment_id):
        comment = self._get_comment(blog_id, comment_id)
        if comment.user != request.user:
            raise PermissionDenied(CommentMessages.EDIT_FORBIDDEN)
        serializer = CommentUpdateSerializer(comment, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(
            data=CommentSerializer(comment).data,
            message=CommentMessages.UPDATED,
        )

    def delete(self, request, blog_id, comment_id):
        comment = self._get_comment(blog_id, comment_id)
        can_delete = (
            comment.user == request.user or
            comment.blog.author == request.user or
            request.user.role == 'admin'
        )
        if not can_delete:
            raise PermissionDenied(CommentMessages.DEL_FORBIDDEN)
        comment.is_deleted = True
        comment.save(update_fields=['is_deleted', 'updated_at'])
        return success_response(message=CommentMessages.DELETED)