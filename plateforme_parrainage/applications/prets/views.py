from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Pret
from .forms import DemandePretForm


@login_required
def pret_list(request):
    qs = Pret.objects.filter(utilisateur=request.user)
    return render(request, 'prets/pret_list.html', {'prets': qs})


@login_required
def pret_detail(request, pk):
    pret = get_object_or_404(Pret, pk=pk, utilisateur=request.user)
    return render(request, 'prets/pret_detail.html', {'pret': pret})


@login_required
def demander_pret(request):
    if request.method == 'POST':
        form = DemandePretForm(request.POST)
        if form.is_valid():
            pret = form.save(commit=False)
            pret.utilisateur = request.user
            pret.statut = 'en_attente'
            pret.save()
            messages.success(request, 'Votre demande de prêt a été soumise.')
            return redirect('prets:list')
    else:
        form = DemandePretForm()
    return render(request, 'prets/demander_pret.html', {'form': form})
