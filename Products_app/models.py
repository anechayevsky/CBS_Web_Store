from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import User
from .utilities import get_timestamp_path
from .utilities import my_slugify
from django_extensions.db.fields import AutoSlugField


class AdvUser(AbstractUser):
    is_activated = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name='Пройшов активацію?')

    class Meta(AbstractUser.Meta):
        pass


class Category(models.Model):
    name = models.CharField(
        max_length=30,
        db_index=True,
        unique=True,
        verbose_name='Назва'
    )
    order = models.SmallIntegerField(
        default=0,
        db_index=True,
        verbose_name='Порядок'
    )
    super_category = models.ForeignKey(
        'SuperCategory',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name='Надкатегорія'
    )


class SuperCategoryManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(super_category__isnull=True)


class SuperCategory(Category):
    objects = SuperCategoryManager()

    def __str__(self):
        return self.name

    class Meta:
        proxy = True
        ordering = ('order', 'name')
        verbose_name = 'Надкатегорія'
        verbose_name_plural = 'Надкатегорії'


class SubCategoryManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(super_category__isnull=False)


class SubCategory(Category):
    objects = SubCategoryManager()

    def __str__(self):
        return f'{self.super_category.name} - {self.name}'

    class Meta:
        proxy = True
        ordering = (
            'super_category__order',
            'super_category__name',
            'order',
            'name'
        )
        verbose_name = 'Підкатегорія'
        verbose_name_plural = 'Підкатегорії'


class Product(models.Model):
    currency_list = (
        (None, '------------------------------'),
        ('грн.', 'UAH'),
        ('долл.', 'USD'),
        ('єв.', 'EUR'),
    )
    p_countries = (
        (None, '------------------------------'),
        ('UA', 'Україна'),
        ('RU', 'Росія'),
        ('PL', 'Польща'),
        ('BL', 'Білорусь'),
        ('CN', 'Китай'),
    )
    slug = AutoSlugField(
        populate_from='title',
        slugify_function=my_slugify
    )
    title = models.CharField(
        max_length=50,
        verbose_name='Назва'
    )
    image = models.ImageField(
        blank=True,
        upload_to=get_timestamp_path,
        verbose_name='Зображення'
    )
    producing_country = models.CharField(
        null=True,
        max_length=24,
        choices=p_countries,
        verbose_name='Країна виробник'
    )
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name='Ціна'
    )
    currency = models.CharField(
        null=True,
        max_length=8,
        choices=currency_list,
        verbose_name='Валюта'
    )
    description = models.TextField(
        max_length=256,
        verbose_name='Опис'
    )
    in_stock = models.BooleanField(
        default=True,
        verbose_name='В наявності'
    )
    published = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Дата додання'
    )
    category = models.ForeignKey(
        to=SubCategory,
        on_delete=models.PROTECT,
        verbose_name='Категорія')

    def delete(self, *args, **kwargs):
        for i in self.additionalimages_set.all():
            i.delete(*args, **kwargs)
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товари'
        ordering = ['-published']


class Comment(models.Model):
    product = models.ForeignKey(
        to=Product,
        on_delete=models.CASCADE,
        verbose_name='Товар'
    )
    author = models.CharField(
        max_length=50,
        verbose_name='Автор'
    )
    text = models.TextField(
        verbose_name='Текст комментаря'
    )
    published = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Опублікований'
    )
    rating = models.IntegerField(
        default=0,
        verbose_name='Рейтинг'
    )

    class Meta:
        verbose_name = 'Коментар'
        verbose_name_plural = 'Коментарі'
        ordering = ['-published']


class CommentRating(models.Model):
    action = (
        ('+', 'plus'),
        ('-', 'minus')
    )
    user = models.ForeignKey(
        to=AdvUser,
        on_delete=models.CASCADE,
        verbose_name='Користувач, який проголосував'
    )
    comment = models.ForeignKey(
        to=Comment,
        on_delete=models.CASCADE,
        verbose_name='Коментар'
    )
    last_action = models.CharField(
        choices=action,
        default=False,
        verbose_name='Остання дія',
        max_length=10
    )
    voted = models.BooleanField(
        default=False,
        verbose_name='Вже голосував?'
    )


class AdditionalImages(models.Model):
    product = models.ForeignKey(
        to=Product,
        on_delete=models.CASCADE,
        verbose_name='Оголошення'
    )
    image = models.ImageField(
        upload_to=get_timestamp_path,
        verbose_name='Зображення'
    )

    class Meta:
        verbose_name = 'Додаткове зображення'
        verbose_name_plural = 'Додаткові зображення'

