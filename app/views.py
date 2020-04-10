from django.shortcuts import render,redirect,reverse
from .models import *
from django.views.generic import View #写类视图
from pure_pagination import Paginator,EmptyPage,PageNotAnInteger
from django.db.models import Q
from django.contrib.auth import authenticate,logout,login
from .forms import *
# Create your views here.

# 创建类视图
class BaseView(View):
    # BlogUser.objects.create_user()
    def get(self,request,*args,**kwargs):
        commets = Comment.objects.filter(is_delete=False).all()

        art_ids = []
        new_commets = []
        for comment in commets:
            if comment.article.id not in art_ids:
                art_ids.append(comment.article.id)
                new_commets.append(comment)
        return new_commets

class IndexView(BaseView):
    def get(self,request,*args,**kwargs):
        new_commets =super().get(request,*args,**kwargs)
        banners = Banner.objects.filter(is_delete=False).all()
        top_article = Article.objects.filter(is_delete=False,is_top=True).all()
        cats = Category.objects.filter(is_delete=False).all()
        all_article = Article.objects.filter(is_delete=False).all()[:10]
        fks = FriendLink.objects.filter(is_delete=False).all()
        count = Article.objects.count() # 日志总数
        return render(request,'index.html',locals())


class ListView(BaseView):
    def get(self,request,*args,**kwargs):

        new_commets =super().get(request,*args,**kwargs)
        all_article = Article.objects.filter(is_delete=False).all()
        tags = Tag.objects.filter(is_delete=False).all()
        try:
            page = request.GET.get('page', 1)
        except PageNotAnInteger:
            page = 1
        p = Paginator(all_article, per_page=1, request=request)
        all_article = p.page(page)
        ctx = {'all_article': all_article}
        return render(request,'list.html',locals())


class DetailView(BaseView):
    def get(self,request,*args,**kwargs):
        count = Article.objects.count()  # 日志总数
        id = kwargs.get('id')
        new_commets = super().get(request, *args, **kwargs)
        try:
            article = Article.objects.get(id=id)
            article.vnum+=1
            article.save()
            # 查找文章的标签
            tags = article.tag.all()
            recommend_articles =[]
            for tag in tags:
                recommend_articles.extend(tag.article_set.all())
            recommend_articles = list(set(recommend_articles ))[:10]# 去重 取前十条

            comments = article.comment_set.all()# 查找评论
            return render(request,'show.html',locals())
        except Article.DoesNotExist:
            return render(request,'404.html')
        # return render(request,'show.html',locals())




class CategoryView(BaseView):
    def get(self,request,*args,**kwargs):
        id = kwargs.get('id')
        new_commets = super().get(request, *args, **kwargs)
        tags = Tag.objects.filter(is_delete=False).all()
        try:
            category = Category.objects.get(id=id)
            all_article = category.article_set.all()
            try:
                page = request.GET.get('page', 1)
            except PageNotAnInteger:
                page = 1
            p = Paginator(all_article, per_page=1, request=request)
            all_article = p.page(page)
            ctx = {'all_article': all_article}
            return render(request,'list.html',locals())
        except Article.DoesNotExist:
            return render(request,'404.html')

class TagView(BaseView):
    def get(self,request,*args,**kwargs):
        id = kwargs.get('id')
        new_commets = super().get(request, *args, **kwargs)
        tags = Tag.objects.filter(is_delete=False).all()
        try:
            tag = Tag.objects.get(id=id)
            all_article = tag.article_set.all()
            # all_article = Article.objects.filter(is_delete=False).all()
            try:
                page = request.GET.get('page', 1)
            except PageNotAnInteger:
                page = 1
            p = Paginator(all_article, per_page=1, request=request)
            all_article = p.page(page)
            ctx = {'all_article': all_article}
            return render(request,'list.html',locals())
        except Article.DoesNotExist:
            return render(request,'404.html')


class SearchView(BaseView):
    def get(self, request, *args, **kwargs):
        try:
            kw = request.GET.get('kw')
            all_article = Article.objects.filter(Q(title__icontains=kw)|Q(content__icontains=kw)).distinct()# 按标题或者内容搜
            try:
                page = request.GET.get('page', 1)
            except PageNotAnInteger:
                page = 1
            p = Paginator(all_article, per_page=1, request=request)
            all_article = p.page(page)
            ctx = {'all_article': all_article}
            return render(request, 'list.html', locals())
        except Article.DoesNotExist:
            return render(request, '404.html')

class LoginView(View):
    def get(self,request,*args,**kwargs):
        login_form = LoginForm()
        return render(request,'login.html',locals())
    def post(self,request,*args,**kwargs):
        login_form = LoginForm(request.POST)
        if login_form.is_valid():
            username = login_form.cleaned_data.get('username')
            pwd = login_form.cleaned_data.get('pwd')
            user = authenticate(request=request,username=username,password=pwd)
            if user:
                login(request,user)
            return redirect(reverse('app:index'))
        else:
            return render(request, 'login.html', locals())

class RegisterView(View):
    def get(self,request,*args,**kwargs):
        reg_form = RegisterForm()
        return render(request,'register.html',locals())
    def post(self,request,*args,**kwargs):
        reg_form = RegisterForm(request.POST)
        if reg_form.is_valid():
            phone = reg_form.cleaned_data.get('phone')
            username = reg_form.cleaned_data.get('username')
            pwd = reg_form.cleaned_data.get('pwd')
            BlogUser.objects.create_user(phone=phone,username=username,password=pwd)
            return redirect(reverse('app:login'))
        else:
            return render(request, 'register.html', locals())
def log_out(request):
    logout(request)
    return redirect(reverse('app:index'))

from django.http import HttpResponse

from django.contrib.auth.decorators import login_required # 验证用户是否登陆过
from django.views.decorators.http import require_http_methods
@require_http_methods(['POST']) # 这个方法只能用post发起请求
@login_required(login_url='/login/')
def comment(request):
    if request.method == 'POST':
        content = request.POST.get('content')
        id = request.POST.get('id')  # 评论文章的id
        if not content:
            return redirect(reverse('app:detail', kwargs={'id': id}))

        user = request.user
        try:
            article = Article.objects.get(id=id)
            Comment.objects.create(content=content, article=article, users=user)
            return redirect(reverse('app:detail',kwargs={'id':id}))
        except Exception as e:
            return render(request,'404.html')
















