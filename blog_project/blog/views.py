from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import PageNumberPagination
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Topic, Blog, Comment
from .serializers import (
    TopicSerializer,
    BlogListSerializer, BlogDetailSerializer, BlogCreateSerializer, BlogUpdateSerializer,
    CommentSerializer, CommentUpdateSerializer,
)
# Cross-app imports — safe, no circular dependency
from users.permissions import IsAdminUser, IsAuthorOrAdmin
from users.utils import success_response, error_response, send_subscriber_emails_async

class TopicListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated(), IsAuthorOrAdmin()]

    def get(self, request):
        topics = Topic.objects.with_blog_count().order_by('name')
        return success_response(data=TopicSerializer(topics, many=True).data)

    def post(self, request):
        serializer = TopicSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return error_response("Topic creation failed.", serializer.errors)
        topic = serializer.save()
        return success_response(
            data=TopicSerializer(topic).data,
            message="Topic created.",
            status_code=status.HTTP_201_CREATED
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
            return error_response("Topic not found.", status_code=status.HTTP_404_NOT_FOUND)
        topic_data         = TopicSerializer(topic).data
        topic_data['blogs'] = BlogListSerializer(
            Blog.objects.filter(topic=topic, is_published=True).select_related('author'),
            many=True
        ).data
        return success_response(data=topic_data)

    def delete(self, request, pk):
        topic = get_object_or_404(Topic, pk=pk)
        try:
            topic.delete()
            return success_response(message="Topic deleted.", status_code=status.HTTP_204_NO_CONTENT)
        except Exception:
            return error_response(
                "Cannot delete — blogs exist under this topic.",
                status_code=status.HTTP_409_CONFLICT
            )


class BlogListCreateView(APIView):
    
    def get_authenticators(self):
        if self.request.method == 'GET':
            return []
        return super().get_authenticators()
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated(), IsAuthorOrAdmin()]

    def get(self, request):
        queryset = Blog.objects.published().select_related('author', 'topic')
        title    = request.query_params.get('title')
        if title:
            queryset = queryset.filter(title__icontains=title)
        return success_response(data=BlogListSerializer(queryset,many=True).data)

    def post(self, request):
        serializer = BlogCreateSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return error_response("Blog creation failed.", serializer.errors)
        blog = serializer.save()
        if blog.is_published:
            send_subscriber_emails_async(blog)
        return success_response(
            data=BlogDetailSerializer(blog).data,
            message="Blog created.",
            status_code=status.HTTP_201_CREATED
        )


class BlogDetailByIdView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, pk):
        return get_object_or_404(Blog.objects.select_related('author', 'topic'), pk=pk)

    def get(self, request, pk):
        blog = self.get_object(pk)
        if not blog.is_published:
            if not request.user.is_authenticated:
                return error_response("This blog is not published yet.", status_code=status.HTTP_403_FORBIDDEN)
            if request.user != blog.author and not request.user.is_admin_user():
                return error_response("This blog is not published yet.", status_code=status.HTTP_403_FORBIDDEN)
        if not request.user.is_authenticated or request.user != blog.author:
            blog.increment_view()
        return success_response(data=BlogDetailSerializer(blog).data)

    def patch(self, request, pk):
        if not request.user.is_authenticated:
            return error_response("Authentication required.", status_code=status.HTTP_401_UNAUTHORIZED)
        blog = self.get_object(pk)
        if request.user != blog.author and not request.user.is_admin_user():
            return error_response("You can only edit your own blogs.", status_code=status.HTTP_403_FORBIDDEN)
        was_draft  = not blog.is_published
        serializer = BlogUpdateSerializer(blog, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response("Update failed.", serializer.errors)
        blog = serializer.save()
        if was_draft and blog.is_published:
            blog.publish()
            blog.save(update_fields=['published_at'])
            send_subscriber_emails_async(blog)
        return success_response(data=BlogDetailSerializer(blog).data, message="Blog updated.")

    def delete(self, request, pk):
        if not request.user.is_authenticated:
            return error_response("Authentication required.", status_code=status.HTTP_401_UNAUTHORIZED)
        blog = self.get_object(pk)
        if request.user != blog.author and not request.user.is_admin_user():
            return error_response("You can only delete your own blogs.", status_code=status.HTTP_403_FORBIDDEN)
        blog.delete()
        return success_response(message="Blog deleted.", status_code=status.HTTP_204_NO_CONTENT)


class BlogDetailBySlugView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug):
        blog = get_object_or_404(Blog.objects.select_related('author', 'topic'), slug=slug)
        if not blog.is_published:
            if not request.user.is_authenticated:
                return error_response("This blog is not published.", status_code=status.HTTP_403_FORBIDDEN)
            if request.user != blog.author and not request.user.is_admin_user():
                return error_response("This blog is not published.", status_code=status.HTTP_403_FORBIDDEN)
        if not request.user.is_authenticated or request.user != blog.author:
            blog.increment_view()
        return success_response(data=BlogDetailSerializer(blog).data)


class BlogPublishToggleView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        blog = get_object_or_404(Blog, pk=pk)
        if request.user != blog.author and not request.user.is_admin_user():
            return error_response("You can only publish your own blogs.", status_code=status.HTTP_403_FORBIDDEN)

        is_published = request.data.get('is_published')
        if is_published is None:
            return error_response("is_published field is required.")

        was_draft = not blog.is_published
        if is_published:
            blog.publish()
        else:
            blog.unpublish()
        blog.save()

        if was_draft and blog.is_published:
            send_subscriber_emails_async(blog)

        return success_response(
            data=BlogDetailSerializer(blog).data,
            message=f"Blog {'published' if blog.is_published else 'unpublished'}."
        )


class BlogsByAuthorView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        from users.models import User
        author   = get_object_or_404(User, pk=pk)
        queryset = Blog.objects.published_by_author(author.id)

        if request.user.is_authenticated:
            if request.user.pk == author.pk or request.user.is_admin_user():
                show = request.query_params.get('is_published')
                if show == 'false':
                    queryset = Blog.objects.by_author(author.id).filter(is_published=False)
                elif show is None:
                    queryset = Blog.objects.by_author(author.id)

        return success_response(data=BlogListSerializer(queryset,many=True).data)

class CommentListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_blog(self, blog_id):
        return get_object_or_404(Blog, pk=blog_id, is_published=True)

    def get(self, request, blog_id):
        blog       = self.get_blog(blog_id)
        comments   = Comment.objects.for_blog(blog.id)
        return success_response(data=CommentSerializer(comments,many=True).data)

    def post(self, request, blog_id):
        blog       = self.get_blog(blog_id)
        serializer = CommentSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return error_response("Comment failed.", serializer.errors)
        comment = serializer.save(blog=blog, user=request.user)
        return success_response(
            data=CommentSerializer(comment).data,
            message="Comment added.",
            status_code=status.HTTP_201_CREATED
        )


class CommentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, blog_id, comment_id):
        return get_object_or_404(Comment, pk=comment_id, blog_id=blog_id, is_deleted=False)

    def patch(self, request, blog_id, comment_id):
        comment = self.get_object(blog_id, comment_id)
        if comment.user != request.user:
            return error_response("You can only edit your own comments.", status_code=status.HTTP_403_FORBIDDEN)
        serializer = CommentUpdateSerializer(comment, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response("Update failed.", serializer.errors)
        serializer.save()
        return success_response(data=CommentSerializer(comment).data, message="Comment updated.")

    def delete(self, request, blog_id, comment_id):
        comment = self.get_object(blog_id, comment_id)
        can_delete = (
            comment.user == request.user or
            comment.blog.author == request.user or
            request.user.is_admin_user()
        )
        if not can_delete:
            return error_response("You cannot delete this comment.", status_code=status.HTTP_403_FORBIDDEN)
        comment.soft_delete()
        return success_response(message="Comment deleted.")
