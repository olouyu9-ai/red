from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView
from .models import ChatGroup, Message, GroupMembership
from .forms import MessageForm, CreateGroupForm
from django.contrib import messages


class GroupListView(ListView):
    model = ChatGroup
    template_name = 'chat/group_list.html'
    context_object_name = 'groups'

    def get_queryset(self):
        # Affiche les groupes auxquels l'utilisateur est membre, ou tous si staff
        user = self.request.user
        if  user.is_authenticated:
            return ChatGroup.objects.all()
        if user.is_staff:
            return ChatGroup.objects.all()
        return ChatGroup.objects.filter(members=user)


class GroupDetailView(DetailView):
    model = ChatGroup
    template_name = 'chat/group_detail.html'
    context_object_name = 'group'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['messages'] = self.object.messages.select_related('sender')[:200]
        ctx['form'] = MessageForm()
        return ctx


@login_required
def create_group(request):
    if request.method == 'POST':
        form = CreateGroupForm(request.POST)
        if form.is_valid():
            group = form.save(commit=False)
            group.created_by = request.user
            group.save()
            GroupMembership.objects.create(user=request.user, group=group, is_admin=True)
            messages.success(request, 'Groupe créé.')
            return redirect('chat:group_detail', pk=group.pk)
    else:
        form = CreateGroupForm()
    return render(request, 'chat/group_create.html', {'form': form})


@login_required
def send_message(request, pk):
    group = get_object_or_404(ChatGroup, pk=pk)
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.group = group
            msg.sender = request.user
            msg.save()
            # mark sender as having read
            msg.read_by.add(request.user)
            return redirect(reverse('chat:group_detail', kwargs={'pk': group.pk}))
    return redirect(reverse('chat:group_detail', kwargs={'pk': group.pk}))
