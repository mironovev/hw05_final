from django.test import TestCase
from django.contrib.auth import get_user_model
from ..models import Group, Post, Comment, Follow

User = get_user_model()


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовое имя группы',
            slug='test_group',
            description='Тестовое описание группы',
        )

    def test_group_str(self):
        '''Метод __str__ возвращает название группы (title)'''
        group = GroupModelTest.group
        self.assertEqual(str(group), 'Тестовое имя группы')


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        user = User.objects.create()
        cls.post = Post.objects.create(
            text='Тестовый текст поста, но относительно длинный',
            author=user
        )

    def test_post_str(self):
        '''Метод __str__ возвращает первые 15 символом текста поста (text)'''
        post = PostModelTest.post
        self.assertEqual(str(post), self.post.text[:15])


class CommentModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        user = User.objects.create()
        cls.post = Post.objects.create(
            text='Тестовый текст поста, но относительно длинный',
            author=user
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=user,
            text='Тестовый текст комментария, но относительно длинный'
        )

    def test_comment_str(self):
        '''Метод __str__ возвращает первые 15 символом текста комментария
        (text)'''
        self.assertEqual(str(self.comment), self.post.text[:15])


class FollowModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = User.objects.create(username='TestUser')
        cls.user2 = User.objects.create(username='TestUser2')
        cls.follow = Follow.objects.create(
            user=cls.user1,
            author=cls.user2
        )

    def test_follow_str(self):
        '''Метод __str__ возвращает информацию о том, на кого
        подписан пользователь'''
        expected_string = (f'{self.user1.username} follows '
                           f'{self.user2.username}')
        self.assertEqual(str(self.follow), expected_string)
