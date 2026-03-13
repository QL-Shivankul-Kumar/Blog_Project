from rest_framework import serializers
from django.utils.text import slugify
from .models import Topic, Blog, Comment
from users.serializers import UserPublicSerializer   # safe cross-app import


class TopicSerializer(serializers.ModelSerializer):
    blog_count = serializers.IntegerField(read_only=True, default=0)
    created_by = UserPublicSerializer(read_only=True)

    class Meta:
        model  = Topic
        fields = ['id', 'name', 'slug', 'created_by', 'blog_count', 'created_at']
        read_only_fields = ['id', 'slug', 'created_by', 'created_at', 'blog_count']

    def validate_name(self, value):
        slug = slugify(value)
        qs = Topic.objects.filter(slug=slug)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A topic with a similar name already exists.")
        return value

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        validated_data['slug'] = slugify(validated_data['name'])
        return super().create(validated_data)

class DeletedUserSerializer(serializers.Serializer):
    def to_representation(self, value):
        if value is None:
            return {'id': None, 'username': 'Deleted User', 'profile_pic': None}
        return UserPublicSerializer(value).data

class BlogListSerializer(serializers.ModelSerializer):
    author = DeletedUserSerializer(read_only=True)
    topic  = TopicSerializer(read_only=True)

    class Meta:
        model  = Blog
        fields = ['id', 'title', 'slug', 'is_published', 'banner_image',
                  'view_count', 'published_at', 'author', 'topic', 'created_at']
        read_only_fields = fields


class BlogDetailSerializer(serializers.ModelSerializer):
    author = DeletedUserSerializer(read_only=True)
    topic  = TopicSerializer(read_only=True)

    class Meta:
        model  = Blog
        fields = ['id', 'title', 'slug', 'content', 'is_published', 'banner_image',
                  'view_count', 'published_at', 'author', 'topic', 'created_at', 'updated_at']
        read_only_fields = fields


class BlogCreateSerializer(serializers.ModelSerializer):
    topic_id = serializers.PrimaryKeyRelatedField(
        queryset=Topic.objects.all(),
        source='topic',
        write_only=True,
        required=False,
        allow_null=True
    )
    topic  = TopicSerializer(read_only=True)
    author = UserPublicSerializer(read_only=True)

    class Meta:
        model  = Blog
        fields = ['id', 'title', 'content', 'is_published', 'banner_image',
                  'topic_id', 'topic', 'author', 'slug', 'published_at', 'created_at']
        read_only_fields = ['id', 'slug', 'author', 'published_at', 'created_at', 'topic']

    def create(self, validated_data):
        from django.utils import timezone
        request = self.context['request']
        validated_data['slug']   = Blog.objects.generate_unique_slug(validated_data['title'])
        validated_data['author'] = request.user
        if validated_data.get('is_published'):
            validated_data['published_at'] = timezone.now()
        return super().create(validated_data)


class BlogUpdateSerializer(serializers.ModelSerializer):
    topic_id = serializers.PrimaryKeyRelatedField(
        queryset=Topic.objects.all(),
        source='topic',
        required=False,
        allow_null=True
    )

    class Meta:
        model  = Blog
        fields = ['title', 'content', 'is_published', 'banner_image', 'topic_id']

class CommentSerializer(serializers.ModelSerializer):
    user = UserPublicSerializer(read_only=True)

    class Meta:
        model  = Comment
        fields = ['id', 'user', 'content', 'is_deleted', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'is_deleted', 'created_at', 'updated_at']

    def validate_content(self, value):
        if not value.strip():
            raise serializers.ValidationError("Comment cannot be empty.")
        if len(value) > 2000:
            raise serializers.ValidationError("Comment cannot exceed 2000 characters.")
        return value.strip()


class CommentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Comment
        fields = ['content']

    def validate_content(self, value):
        if not value.strip():
            raise serializers.ValidationError("Comment cannot be empty.")
        return value.strip()
