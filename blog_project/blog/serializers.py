from rest_framework import serializers
from django.utils.text import slugify
from .models import Topic, Blog, Comment
from users.serializers import UserPublicSerializer

class AuthorBriefSerializer(serializers.Serializer):
    def to_representation(self, value):
        if value is None:
            return {'id': None, 'username': 'Deleted User', 'profile_pic': None}
        return {
            'id':          value.id,
            'username':    value.username,
            'profile_pic': value.profile_pic.url if value.profile_pic else None,
        }


class TopicBriefSerializer(serializers.Serializer):
    def to_representation(self, value):
        if value is None:
            return None
        return {
            'id':   value.id,
            'name': value.name,
            'slug': value.slug,
        }


class CreatedByBriefSerializer(serializers.Serializer):
    def to_representation(self, value):
        if value is None:
            return {'id': None, 'username': 'Deleted User'}
        return {
            'id':       value.id,
            'username': value.username,
        }

class TopicSerializer(serializers.ModelSerializer):
    blog_count = serializers.IntegerField(read_only=True, default=0)
    created_by = CreatedByBriefSerializer(read_only=True)
    class Meta:
        model  = Topic
        fields = ['id', 'name', 'slug', 'created_by', 'blog_count', 'created_at']
        read_only_fields = ['id', 'slug', 'created_by', 'created_at', 'blog_count']

    def validate_name(self, value):
        # strip whitespace first
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Topic name cannot be empty.")
        if len(value) < 2:
            raise serializers.ValidationError("Topic name must be at least 2 characters.")
        slug = slugify(value)
        if not slug:
            raise serializers.ValidationError("Topic name must contain valid characters.")
        qs = Topic.objects.filter(slug=slug)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A topic with a similar name already exists.")

        return value

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        validated_data['slug']       = slugify(validated_data['name'])
        return super().create(validated_data)


class DeletedUserSerializer(serializers.Serializer):
    def to_representation(self, value):
        if value is None:
            return {'id': None, 'username': 'Deleted User', 'profile_pic': None}
        return UserPublicSerializer(value).data


class BlogListSerializer(serializers.ModelSerializer):
    author = AuthorBriefSerializer(read_only=True)
    topic  = TopicBriefSerializer(read_only=True)
    class Meta:
        model  = Blog
        fields = ['id', 'title', 'slug', 'is_published', 'banner_image',
                  'view_count', 'published_at', 'author', 'topic', 'created_at']
        read_only_fields = fields

class BlogDetailSerializer(serializers.ModelSerializer):
    author = DeletedUserSerializer(read_only=True)
    topic  = TopicBriefSerializer(read_only=True)
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
    topic  = TopicBriefSerializer(read_only=True)
    author = AuthorBriefSerializer(read_only=True)
    class Meta:
        model  = Blog
        fields = ['id', 'title', 'content', 'is_published', 'banner_image',
                  'topic_id', 'topic', 'author', 'slug', 'published_at', 'created_at']
        read_only_fields = ['id', 'slug', 'author', 'published_at', 'created_at', 'topic']

    def validate_title(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Blog title cannot be empty.")
        if len(value) < 3:
            raise serializers.ValidationError("Blog title must be at least 3 characters.")
        return value

    def validate_content(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Blog content cannot be empty.")
        if len(value) < 10:
            raise serializers.ValidationError("Blog content must be at least 10 characters.")
        return value

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

    def validate_title(self, value):
        # only runs if title is included in the PATCH body
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Blog title cannot be empty.")
        if len(value) < 3:
            raise serializers.ValidationError("Blog title must be at least 3 characters.")
        return value

    def validate_content(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Blog content cannot be empty.")
        if len(value) < 10:
            raise serializers.ValidationError("Blog content must be at least 10 characters.")
        return value

class CommentSerializer(serializers.ModelSerializer):
    user = AuthorBriefSerializer(read_only=True)
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
        if len(value) > 2000:
            raise serializers.ValidationError("Comment cannot exceed 2000 characters.")
        return value.strip()