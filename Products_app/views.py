from django.urls import reverse_lazy, reverse
from django.http import Http404
from django.db.models import Q
from django.template.loader import get_template
from django.template import TemplateDoesNotExist
from django.shortcuts import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordChangeView
from django.contrib.auth.views import LoginView
from django.contrib.auth.views import LogoutView
from django.contrib.auth import logout
from django.contrib import messages
from django.views.generic import ListView
from django.views.generic import UpdateView
from django.views.generic import CreateView
from django.views.generic import DeleteView
from django.views.generic import TemplateView
from django.views.generic import DetailView
from django.core.paginator import Paginator

from .models import AdvUser
from .models import Product
from .models import AdditionalImages
from .models import Category
from .models import SubCategory
from .models import Comment
from .models import CommentRating

from .forms import ChangeUserInfoForm
from .forms import RegisterUserForm
from .forms import SearchForm
from .forms import UserCommentForm

from cart.forms import CartAddProductForm


def other_page(request, page):
    """
    Redirecting to additional pages of the site,
    for example "About us" or "user agreement"
    """
    try:
        template = get_template(page + '.html')
    except TemplateDoesNotExist:
        raise Http404
    return HttpResponse(template.render(request=request))


class RegisterUserView(CreateView):
    """
    User registration page
    """
    model = AdvUser
    template_name = 'register_user.html'
    form_class = RegisterUserForm
    success_url = reverse_lazy('products:reg_successful')


class RegisterSuccessfulView(TemplateView):
    """
    The page to which successfully
    registered users are redirected
    """
    template_name = 'register_successful.html'


@login_required
def profile(request):
    """
    User profile page.

    Decorator @login_required is necessary so
    that unauthorized users cannot get to this page.
    """
    return render(request, 'profile.html')


class PLoginView(LoginView):
    """
    User login page
    """
    template_name = 'login.html'
    success_url = reverse_lazy('products:index')


class PLogoutView(LoginRequiredMixin, LogoutView):
    template_name = 'logout.html'


class ChangeUserInfoView(SuccessMessageMixin, LoginRequiredMixin, UpdateView):
    """
    Displaying a form for changing information by the user
    """
    model = AdvUser
    template_name = 'change_user_info.html'
    form_class = ChangeUserInfoForm
    success_url = reverse_lazy('products:profile')
    success_message = 'Інформацію про користувача змінено'

    def dispatch(self, request, *args, **kwargs):
        self.user_id = request.user.pk
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        if not queryset:
            queryset = self.get_queryset()
        return get_object_or_404(queryset,
                                 pk=self.user_id)


class PChangePasswordView(SuccessMessageMixin, LoginRequiredMixin, PasswordChangeView):
    template_name = 'change_password.html'
    success_url = reverse_lazy('products:profile')
    success_message = 'Пароль успішно змінено'


class PDeleteUserView(LoginRequiredMixin,
                      DeleteView):
    model = AdvUser
    template_name = 'delete_user.html'
    success_url = reverse_lazy('products:index')

    def dispatch(self, request, *args, **kwargs):
        self.user_id = request.user.pk
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        logout(request)
        messages.add_message(request, messages.SUCCESS,
                             'Користувач видалений')
        return super().post(request, *args, **kwargs)

    def get_object(self, queryset=None):
        if not queryset:
            queryset = self.get_queryset()
        return get_object_or_404(queryset,
                                 pk=self.user_id)


def search_keyword(request, products_obj):
    """Search for matches by keyword"""
    keyword = ''
    products = products_obj
    if 'search_keyword' in request.GET:
        keyword = request.GET['search_keyword']
        q = Q(title__contains=keyword) | Q(description__contains=keyword)
        products = products_obj.filter(q)
    return {'keyword': keyword,
            'products': products}


def my_paginator(request, objects, items_in_page=1):
    paginator = Paginator(objects, items_in_page)
    if 'page' in request.GET:
        page_number = request.GET['page']
    else:
        page_number = 1
    return paginator.get_page(page_number)


def index(request):
    """
    Home page of the site with a list of products
    """
    template = 'index.html'
    keyword = search_keyword(request=request,
                             products_obj=Product.objects.all())
    form = SearchForm(initial={
        'search_keyword': keyword['keyword']
    })
    page = my_paginator(request=request,
                        objects=keyword['products'],
                        items_in_page=3)
    context = {
        'products': page.object_list,
        'form': form,
        'page': page
    }

    return render(request, template, context=context)


class InCategoryView(ListView):
    """in category"""
    template_name = 'in_category.html'
    model = Product

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        category_pk = self.kwargs['pk']
        keyword = search_keyword(request=self.request,
                                 products_obj=self.model.objects.filter(category__super_category_id=category_pk))
        form = SearchForm(initial={
            'search_keyword': keyword['keyword'],
        })
        page = my_paginator(request=self.request,
                            objects=keyword['products'],
                            items_in_page=2)
        context['sub_categories'] = SubCategory.objects.filter(super_category_id=category_pk)
        context['category'] = Category.objects.get(pk=category_pk)
        context['products'] = page.object_list
        context['form'] = form
        context['page'] = page
        return context


class InSubCategoryView(ListView):
    template_name = 'in_sub_category.html'
    model = Product
    context_object_name = 'products'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        sub_category_pk = self.kwargs['pk']
        keyword = search_keyword(request=self.request,
                                 products_obj=self.model.objects.filter(category_id=sub_category_pk))
        form = SearchForm(initial={
            'search_keyword': keyword['keyword']
            })
        page = my_paginator(request=self.request,
                            objects=keyword['products'],
                            items_in_page=2)
        category = SubCategory.objects.get(pk=sub_category_pk)
        context['sub_category'] = category
        context['sub_categories'] = SubCategory.objects.filter(super_category_id=category.super_category.pk)
        context['products'] = page.object_list
        context['form'] = form
        context['page'] = page
        return context


class ProductDetailView(DetailView):
    template_name = 'product_detail.html'
    model = Product

    def get_object(self, queryset=None):
        return get_object_or_404(self.model, slug=self.kwargs['slug'])

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        other_images = AdditionalImages.objects.filter(product_id=self.object.pk)
        initial = {'product': self.object,
                   'author': self.request.user.username}
        comments = Comment.objects.filter(product=self.object)
        comment_page = my_paginator(request=self.request, objects=comments, items_in_page=4)
        context['cart_form'] = CartAddProductForm()
        context['page'] = comment_page
        context['comments'] = comment_page.object_list
        context['comment_form'] = UserCommentForm(initial=initial)
        context['images'] = other_images
        return context

    def _add_product_to_viewed_container(self, container, request):
        container.append(self.object.slug)
        request.session['viewed'] = container
        return request

    def _check_not_duplicate(self, container):
        if not container:
            return True
        prev_elem = len(container) - 1
        if container[prev_elem] == self.object.slug:
            return False
        else:
            return True

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        viewed = request.session.get('viewed', [])
        if self._check_not_duplicate(viewed):
            if len(viewed) >= 5:
                viewed.pop(0)
            self._add_product_to_viewed_container(viewed, request)
        return response

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data()
        form = None
        if 'add_comment' in self.request.POST and \
            self.request.user.is_authenticated:
            form = UserCommentForm(self.request.POST)
            if form.is_valid():
                form.save()
                messages.add_message(request=self.request, level=messages.SUCCESS,
                                     message='Коментар додано')
            else:
                messages.add_message(request=self.request, level=messages.ERROR,
                                     message='Виникла помилка під час додавання коментаря')
        else:
            messages.add_message(request=self.request, level=messages.WARNING,
                                 message='Щоб залишити коментар, вам потрібно'
                                         ' зареєструватися або увійти у свій акаунт.')
        context['form'] = form
        return self.render_to_response(context)


def save_changes_after_vote_on_comment(comment, comment_action, comment_rating_obj, cro_last_action, cro_voted):
    """
    Helper function to comment_rating for saving changes
    """
    if comment_action == '+':
        comment.rating += 1
    else:
        comment.rating -= 1
    comment_rating_obj.last_action = cro_last_action
    comment_rating_obj.voted = cro_voted
    comment_rating_obj.save()
    comment.save()


def comment_rating(request, **kwargs):
    """
    Changing the rating of comments.

    -The user must be registered.
    -The value can be increased or decreased by one.
    -User can cancel or change his choice.
    """
    if request.user.is_authenticated:
        comment = Comment.objects.get(pk=kwargs['comment_pk'])
        comment_rating_object = CommentRating.objects.get_or_create(user=request.user, comment=comment)
        if kwargs['action'] == 'plus':
            if comment_rating_object[0].voted:
                if comment_rating_object[0].last_action == 'plus':
                    messages.add_message(
                        request,
                        level=messages.WARNING,
                        message='Ви не можете проголосувати двічі за один коментар.')
                elif comment_rating_object[0].last_action == 'minus':
                    messages.add_message(
                        request,
                        level=messages.WARNING,
                        message='Голос скасовано.'
                    )
                    save_changes_after_vote_on_comment(comment, '+', comment_rating_object[0], False, False)
            else:
                save_changes_after_vote_on_comment(comment, '+', comment_rating_object[0], 'plus', True)
                messages.add_message(
                    request,
                    level=messages.SUCCESS,
                    message='Голос зараховано.'
                    )
        elif kwargs['action'] == 'minus':
            if comment_rating_object[0].voted:
                if comment_rating_object[0].last_action == 'minus':
                    messages.add_message(
                        request,
                        level=messages.WARNING,
                        message='Ви не можете проголосувати двічі за один коментар.'
                    )
                elif comment_rating_object[0].last_action == 'plus':
                    save_changes_after_vote_on_comment(comment, '-', comment_rating_object[0], 'minus', False)
                    messages.add_message(
                        request,
                        level=messages.WARNING,
                        message='Голос скасовано.'
                    )
            else:
                save_changes_after_vote_on_comment(comment, '-', comment_rating_object[0], 'minus', True)
                messages.add_message(
                    request,
                    level=messages.SUCCESS,
                    message='Голос зараховано.'
                )
    else:
        messages.add_message(
            request,
            level=messages.ERROR,
            message='Для оцінки коментарів увійдіть у свій акаунт')

    return HttpResponseRedirect(reverse_lazy('products:product_detail',  kwargs={'slug': kwargs['slug']}))


def delete_comment(request, **kwargs):
    """
    Method for user to delete his comment.
    User must be logged in.
    """
    comment = Comment.objects.get(pk=kwargs['comment_pk'])
    if request.user.username == comment.author:
        comment.delete()
        messages.add_message(request, level=messages.SUCCESS, message='Коментар видалено.')
    if 'slug' in kwargs:
        return HttpResponseRedirect(reverse_lazy('products:product_detail', kwargs={'slug': kwargs['slug']}))
    else:
        return HttpResponseRedirect(reverse('products:user_comments'))


@login_required()
def user_comments(request):
    """
    Page of all user comments
    """
    template = 'user_comments.html'
    comments = Comment.objects.filter(author=request.user)
    return render(request, template_name=template, context={'comments': comments})
