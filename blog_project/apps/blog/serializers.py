from rest_framework import serializers
from django.utils.text import slugify
from .models import Topic, Blog, Comment


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
        return {'id': value.id, 'name': value.name, 'slug': value.slug}


class CreatedByBriefSerializer(serializers.Serializer):
    def to_representation(self, value):
        if value is None:
            return {'id': None, 'username': 'Deleted User'}
        return {'id': value.id, 'username': value.username}


class TopicSerializer(serializers.ModelSerializer):
    blog_count = serializers.IntegerField(read_only=True, default=0)
    created_by = CreatedByBriefSerializer(read_only=True)

    class Meta:
        model  = Topic
        fields = ['id', 'name', 'slug', 'created_by', 'blog_count', 'created_at']
        read_only_fields = ['id', 'slug', 'created_by', 'created_at', 'blog_count']

    def validate(self, data):
        errors = {}
        name   = data.get('name', '').strip()

        if not name:
            errors['name'] = "Topic name cannot be empty."
        elif len(name) < 2:
            errors['name'] = "Topic name must be at least 2 characters."
        else:
            slug = slugify(name)
            if not slug:
                errors['name'] = "Topic name must contain valid characters."
            else:
                qs = Topic.objects.filter(slug=slug)
                if self.instance:
                    qs = qs.exclude(pk=self.instance.pk)
                if qs.exists():
                    errors['name'] = "A topic with a similar name already exists."

        if errors:
            raise serializers.ValidationError(errors)

        data['name'] = name
        return data


class BlogListSerializer(serializers.ModelSerializer):
    author = AuthorBriefSerializer(read_only=True)
    topic  = TopicBriefSerializer(read_only=True)

    class Meta:
        model  = Blog
        fields = ['id', 'title', 'slug', 'is_published', 'banner_image',
                  'view_count', 'published_at', 'author', 'topic', 'created_at']
        read_only_fields = fields


class BlogInTopicSerializer(serializers.ModelSerializer):
    author = AuthorBriefSerializer(read_only=True)

    class Meta:
        model  = Blog
        fields = ['id', 'title', 'slug', 'banner_image',
                  'view_count', 'published_at', 'author', 'created_at']
        read_only_fields = fields


class BlogDetailSerializer(serializers.ModelSerializer):
    author = AuthorBriefSerializer(read_only=True)
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
        allow_null=True,
    )
    topic  = TopicBriefSerializer(read_only=True)
    author = AuthorBriefSerializer(read_only=True)

    class Meta:
        model  = Blog
        fields = ['id', 'title', 'content', 'is_published', 'banner_image',
                  'topic_id', 'topic', 'author', 'slug', 'published_at', 'created_at']
        read_only_fields = ['id', 'slug', 'author', 'published_at', 'created_at', 'topic']

    def validate(self, data):
        errors  = {}
        title   = data.get('title', '').strip()
        content = data.get('content', '').strip()

        if not title:
            errors['title'] = "Blog title cannot be empty."
        elif len(title) < 3:
            errors['title'] = "Blog title must be at least 3 characters."

        if not content:
            errors['content'] = "Blog content cannot be empty."
        elif len(content) < 10:
            errors['content'] = "Blog content must be at least 10 characters."

        if errors:
            raise serializers.ValidationError(errors)

        data['title']   = title
        data['content'] = content
        return data


class BlogUpdateSerializer(serializers.ModelSerializer):
    topic_id = serializers.PrimaryKeyRelatedField(
        queryset=Topic.objects.all(),
        source='topic',
        required=False,
        allow_null=True,
    )

    class Meta:
        model  = Blog
        fields = ['title', 'content', 'is_published', 'banner_image', 'topic_id']

    def validate(self, data):
        errors  = {}
        title   = data.get('title', '').strip() if 'title' in data else None
        content = data.get('content', '').strip() if 'content' in data else None

        if title is not None:
            if not title:
                errors['title'] = "Blog title cannot be empty."
            elif len(title) < 3:
                errors['title'] = "Blog title must be at least 3 characters."
            else:
                data['title'] = title

        if content is not None:
            if not content:
                errors['content'] = "Blog content cannot be empty."
            elif len(content) < 10:
                errors['content'] = "Blog content must be at least 10 characters."
            else:
                data['content'] = content

        if errors:
            raise serializers.ValidationError(errors)

        return data


class CommentSerializer(serializers.ModelSerializer):
    user = AuthorBriefSerializer(read_only=True)

    class Meta:
        model  = Comment
        fields = ['id', 'user', 'content', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def validate(self, data):
        errors  = {}
        content = data.get('content', '').strip()

        if not content:
            errors['content'] = "Comment cannot be empty."
        elif len(content) > 2000:
            errors['content'] = "Comment cannot exceed 2000 characters."

        if errors:
            raise serializers.ValidationError(errors)

        data['content'] = content
        return data


class CommentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Comment
        fields = ['content']

    def validate(self, data):
        errors  = {}
        content = data.get('content', '').strip()

        if not content:
            errors['content'] = "Comment cannot be empty."
        elif len(content) > 2000:
            errors['content'] = "Comment cannot exceed 2000 characters."

        if errors:
            raise serializers.ValidationError(errors)

        data['content'] = content
        return data