from copy import deepcopy
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.text import slugify
from django.views.decorators.http import require_http_methods, require_safe, require_POST
from guardian.shortcuts import get_groups_with_perms
from harnas.contest.forms import GroupForm
from guardian.shortcuts import assign_perm, get_users_with_perms
from harnas.contest.models import Contest, Task
from harnas.contest.forms import ContestForm, NewsForm, TaskFetchForm


@require_safe
def index(request):
    return render(request, 'contest/contest_index.html')


@require_safe
@login_required
def details(request, id, tab='news'):
    contest = Contest.objects.get(pk=id)
    if not request.user.has_perm('contest.view_contest', contest):
        raise PermissionDenied
    contest_form = ContestForm(instance=contest)
    groups = get_groups_with_perms(contest, attach_perms=True)
    groups = [k for k, v in groups.items() if 'view_contest' in v]
    group_form = GroupForm()
    news = contest.news_set.all().order_by('-created_at')
    news_form = NewsForm()
    fetch_task_form = TaskFetchForm()
    if request.user.has_perm('contest.manage_contest', contest):
        participants = get_users_with_perms(contest, attach_perms=True)
        participants = [k for k, v in participants.items()
                        if 'participate_in_contest' in v]
    else:
        participants = []
    tasks = Task.objects.filter(contest=contest)
    return render(request, 'contest/contest_details.html',
                  { 'contest': contest,
                    'contest_form': contest_form,
                    'groups': groups,
                    'group_form': group_form,
                    'participants': participants,
                    'news': news,
                    'news_form': news_form,
                    'fetch_task_form': fetch_task_form,
                    'tasks': tasks,
                    'tab': tab,
                    })


@require_http_methods(['GET', 'POST'])
@login_required
def edit(request, id=None):
    if id:
        contest = Contest.objects.get(pk=id)
        form_post = reverse('contest_edit', args=[id])
        if not request.user.has_perm('contest.manage_contest', contest):
            messages.add_message(request, messages.ERROR, "You cannot do that.")
            return HttpResponseRedirect('/')
    else:
        contest = Contest()
        form_post = reverse('contest_new')
        if not request.user.has_perm('contest.add_contest'):
            messages.add_message(request, messages.ERROR, "You cannot do that.")
            return HttpResponseRedirect('/')
    if request.method == 'POST':
        form = ContestForm(request.POST, instance=contest)
    else:
        form = ContestForm(instance=contest)
    if form.is_valid():
        new_contest = form.save(commit=False)
        new_contest.slug = slugify(new_contest.name)
        if id is None:
            new_contest.creator_id = request.user.pk
        new_contest.save()
        assign_perm('contest.manage_contest', request.user, new_contest)
        assign_perm('contest.view_contest', request.user, new_contest)
        cache_key = make_template_fragment_key('contest_description',
                                               [new_contest.pk])
        cache.delete(cache_key)
        messages.add_message(request, messages.SUCCESS, "New contest has been successfully created.")
        return HttpResponseRedirect(reverse('contest_details',
                                            args=[new_contest.pk]))

    return render(request, 'contest/contest_new.html',
                  { 'form': form,
                    'form_post': form_post })


@require_POST
@login_required
def fetch_task(request, id):
    contest = Contest.objects.get(pk=id)
    if not request.user.has_perm('manage_contest', contest):
        messages.add_message(request, messages.ERROR, "You cannot do that.")
    if request.method == 'POST':
        form = TaskFetchForm(request.POST)
        if form.is_valid():
            parent_task = form.cleaned_data['task']
            fetched_task = deepcopy(parent_task)
            fetched_task.pk = None
            fetched_task.contest = contest
            fetched_task.parent = parent_task
            fetched_task.save()
            messages.add_message(request, messages.SUCCESS, "New task has been added to contest %s."
                                 % contest.name)

    return HttpResponseRedirect(reverse('contest_details',
                                        args=[id, 'tasks']))
