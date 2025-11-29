from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, get_user_model
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q

from .forms import SetupMasterForm, UserForm
from .models import Protocolo, Cliente

User = get_user_model()


# ========== DECORATORS DE PERMISSÃO ==========

def is_master(user):
    """Verifica se o usuário tem role MASTER."""
    return user.is_authenticated and user.role == User.Role.MASTER


def master_required(view_func):
    """Decorator que restringe acesso apenas a usuários MASTER."""
    decorated_view = user_passes_test(
        is_master,
        login_url='home',
        redirect_field_name=None
    )(view_func)
    return decorated_view


# ========== AUTENTICAÇÃO ==========

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


# ========== HOME / DASHBOARD ==========

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


# ========== CRUD DE USUÁRIOS ==========

@login_required
@master_required
def user_list(request):
    """Lista todos os usuários do sistema."""
    users = User.objects.all().order_by('-date_joined')
    
    # Busca por nome ou username
    search = request.GET.get('search', '').strip()
    if search:
        users = users.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(username__icontains=search) |
            Q(email__icontains=search)
        )
    
    # Filtro por role
    role_filter = request.GET.get('role', '')
    if role_filter:
        users = users.filter(role=role_filter)
    
    # Filtro por status
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    
    # Paginação
    paginator = Paginator(users, 20)
    page = request.GET.get('page', 1)
    users_page = paginator.get_page(page)
    
    context = {
        'users': users_page,
        'search': search,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'roles': User.Role.choices,
    }
    
    return render(request, 'core/user_list.html', context)


@login_required
@master_required
def user_create(request):
    """Cria um novo usuário."""
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Usuário "{user.username}" criado com sucesso!')
            return redirect('user_list')
    else:
        form = UserForm()
    
    context = {
        'form': form,
        'title': 'Novo Usuário',
        'button_text': 'Criar Usuário',
    }
    
    return render(request, 'core/user_form.html', context)


@login_required
@master_required
def user_update(request, pk):
    """Edita um usuário existente."""
    user_obj = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user_obj)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Usuário "{user.username}" atualizado com sucesso!')
            return redirect('user_list')
    else:
        form = UserForm(instance=user_obj)
    
    context = {
        'form': form,
        'user_obj': user_obj,
        'title': f'Editar Usuário: {user_obj.username}',
        'button_text': 'Salvar Alterações',
    }
    
    return render(request, 'core/user_form.html', context)


@login_required
@master_required
def user_delete(request, pk):
    """Remove um usuário do sistema."""
    user_obj = get_object_or_404(User, pk=pk)
    
    # Impede que o usuário delete a si mesmo
    if user_obj == request.user:
        messages.error(request, 'Você não pode excluir sua própria conta.')
        return redirect('user_list')
    
    if request.method == 'POST':
        username = user_obj.username
        user_obj.delete()
        messages.success(request, f'Usuário "{username}" excluído com sucesso!')
        return redirect('user_list')
    
    # Se não for POST, redireciona para a lista
    return redirect('user_list')
