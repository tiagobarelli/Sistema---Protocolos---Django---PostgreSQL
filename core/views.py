from django.shortcuts import render, redirect
from django.contrib.auth import login, get_user_model
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .forms import SetupMasterForm
from .models import Protocolo, Cliente

User = get_user_model()


class CustomLoginView(LoginView):
    template_name = 'core/login.html'
    redirect_authenticated_user = True

    def dispatch(self, request, *args, **kwargs):
        # VERIFICAÇÃO DE SEGURANÇA: Se não há usuários, força o setup
        if not User.objects.exists():
            return redirect('setup_system')
        return super().dispatch(request, *args, **kwargs)


def setup_system(request):
    """
    View de Instalação: Só funciona se não houver NENHUM usuário no banco.
    """
    if User.objects.exists():
        messages.warning(request, "O sistema já possui um administrador configurado.")
        return redirect('login')

    if request.method == 'POST':
        form = SetupMasterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Loga o usuário automaticamente após criar
            login(request, user)
            messages.success(request, f"Sistema configurado! Bem-vindo, {user.first_name}.")
            return redirect('home')
    else:
        form = SetupMasterForm()

    return render(request, 'core/setup.html', {'form': form})


@login_required
def home(request):
    """
    View da página inicial (Dashboard) com estatísticas.
    """
    today = timezone.localdate()
    
    # Estatísticas de Protocolos por Status
    stats = {
        'em_andamento': Protocolo.objects.filter(
            status=Protocolo.StatusProtocolo.EM_ANDAMENTO
        ).count(),
        'escritura_finalizada': Protocolo.objects.filter(
            status=Protocolo.StatusProtocolo.ESCRITURA_FINALIZADA
        ).count(),
        'concluido': Protocolo.objects.filter(
            status=Protocolo.StatusProtocolo.CONCLUIDO
        ).count(),
        'cancelado': Protocolo.objects.filter(
            status=Protocolo.StatusProtocolo.CANCELADO
        ).count(),
        'clientes': Cliente.objects.count(),
    }
    
    # Agendamentos do dia
    agendamentos = Protocolo.objects.filter(
        data_agendamento=today,
        status=Protocolo.StatusProtocolo.EM_ANDAMENTO
    ).select_related('tipo_ato').order_by('horario_agendamento')[:5]
    
    context = {
        'today': today,
        'stats': stats,
        'agendamentos': agendamentos,
    }
    
    return render(request, 'core/home.html', context)
