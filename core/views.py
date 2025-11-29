import re
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, get_user_model
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .forms import (
    SetupMasterForm,
    UserForm,
    TabelionatoForm,
    TipoAtoForm,
    ClienteForm,
    ProtocoloCertidaoForm,
)
from .models import Protocolo, Cliente, Tabelionato, TipoAto

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


# ========== CONFIGURAÇÕES DO SISTEMA ==========

@login_required
@master_required
def settings_view(request):
    """
    View principal de configurações com abas:
    - Aba 1: Dados do Tabelionato (Singleton)
    - Aba 2: Tipos de Atos
    """
    # Recupera ou cria instância do Tabelionato (Singleton)
    tabelionato = Tabelionato.objects.first()
    
    # Determina qual aba está ativa
    active_tab = request.GET.get('tab', 'tabelionato')
    
    # Formulário do Tabelionato
    if request.method == 'POST' and 'save_tabelionato' in request.POST:
        if tabelionato:
            tabelionato_form = TabelionatoForm(request.POST, instance=tabelionato)
        else:
            tabelionato_form = TabelionatoForm(request.POST)
        
        if tabelionato_form.is_valid():
            tabelionato_form.save()
            messages.success(request, 'Dados do Tabelionato salvos com sucesso!')
            return redirect('settings_view')
    else:
        if tabelionato:
            tabelionato_form = TabelionatoForm(instance=tabelionato)
        else:
            tabelionato_form = TabelionatoForm()
    
    # Lista de Tipos de Ato
    tipos_ato = TipoAto.objects.all().order_by('nome')
    
    context = {
        'tabelionato_form': tabelionato_form,
        'tabelionato': tabelionato,
        'tipos_ato': tipos_ato,
        'active_tab': active_tab,
    }
    
    return render(request, 'core/settings.html', context)


@login_required
@master_required
def tipo_ato_create(request):
    """Cria um novo Tipo de Ato."""
    if request.method == 'POST':
        form = TipoAtoForm(request.POST)
        if form.is_valid():
            tipo_ato = form.save()
            messages.success(request, f'Tipo de Ato "{tipo_ato.nome}" criado com sucesso!')
            return redirect('settings_view')
    else:
        form = TipoAtoForm()
    
    context = {
        'form': form,
        'title': 'Novo Tipo de Ato',
        'button_text': 'Criar',
    }
    
    return render(request, 'core/tipo_ato_form.html', context)


@login_required
@master_required
def tipo_ato_update(request, pk):
    """Edita um Tipo de Ato existente."""
    tipo_ato = get_object_or_404(TipoAto, pk=pk)
    
    if request.method == 'POST':
        form = TipoAtoForm(request.POST, instance=tipo_ato)
        if form.is_valid():
            tipo_ato = form.save()
            messages.success(request, f'Tipo de Ato "{tipo_ato.nome}" atualizado com sucesso!')
            return redirect('settings_view')
    else:
        form = TipoAtoForm(instance=tipo_ato)
    
    context = {
        'form': form,
        'tipo_ato': tipo_ato,
        'title': f'Editar: {tipo_ato.nome}',
        'button_text': 'Salvar Alterações',
    }
    
    return render(request, 'core/tipo_ato_form.html', context)


@login_required
@master_required
def tipo_ato_delete(request, pk):
    """Exclui um Tipo de Ato (exclusão física)."""
    tipo_ato = get_object_or_404(TipoAto, pk=pk)
    
    if request.method == 'POST':
        nome = tipo_ato.nome
        tipo_ato.delete()
        messages.success(request, f'Tipo de Ato "{nome}" excluído com sucesso!')
        return redirect('settings_view')
    
    return redirect('settings_view')


@login_required
@master_required
def tipo_ato_toggle(request, pk):
    """Alterna o status ativo/inativo de um Tipo de Ato."""
    tipo_ato = get_object_or_404(TipoAto, pk=pk)
    
    if request.method == 'POST':
        tipo_ato.ativo = not tipo_ato.ativo
        tipo_ato.save()
        status = 'ativado' if tipo_ato.ativo else 'desativado'
        messages.success(request, f'Tipo de Ato "{tipo_ato.nome}" {status} com sucesso!')
    
    return redirect('settings_view')


# ========== CRUD DE CLIENTES ==========

@login_required
def cliente_list(request):
    """Lista todos os clientes com busca e paginação."""
    clientes = Cliente.objects.all().order_by('nome')
    
    # Busca por nome, CPF ou CNPJ
    search = request.GET.get('search', '').strip()
    if search:
        clientes = clientes.filter(
            Q(nome__icontains=search) |
            Q(cpf__icontains=search) |
            Q(cnpj__icontains=search) |
            Q(email__icontains=search)
        )
    
    # Filtro por tipo de pessoa
    tipo_filter = request.GET.get('tipo', '')
    if tipo_filter:
        clientes = clientes.filter(tipo_pessoa=tipo_filter)
    
    # Paginação
    paginator = Paginator(clientes, 20)
    page = request.GET.get('page', 1)
    clientes_page = paginator.get_page(page)
    
    context = {
        'clientes': clientes_page,
        'search': search,
        'tipo_filter': tipo_filter,
        'tipos_pessoa': Cliente.TipoPessoa.choices,
    }
    
    return render(request, 'core/cliente_list.html', context)


@login_required
def cliente_create(request):
    """Cria um novo cliente."""
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save()
            messages.success(request, f'Cliente "{cliente.nome}" cadastrado com sucesso!')
            return redirect('cliente_list')
    else:
        form = ClienteForm()
    
    context = {
        'form': form,
        'title': 'Novo Cliente',
        'button_text': 'Cadastrar Cliente',
    }
    
    return render(request, 'core/cliente_form.html', context)


@login_required
def cliente_update(request, pk):
    """Edita um cliente existente."""
    cliente = get_object_or_404(Cliente, pk=pk)
    
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            cliente = form.save()
            messages.success(request, f'Cliente "{cliente.nome}" atualizado com sucesso!')
            return redirect('cliente_list')
    else:
        form = ClienteForm(instance=cliente)
    
    context = {
        'form': form,
        'cliente': cliente,
        'title': f'Editar Cliente: {cliente.nome}',
        'button_text': 'Salvar Alterações',
    }
    
    return render(request, 'core/cliente_form.html', context)


# ========== API - BUSCA DE CLIENTE ==========

@login_required
@require_GET
def api_buscar_cliente(request):
    """
    API para buscar cliente por CPF ou CNPJ.
    Retorna dados completos do cliente para autopreenchimento.
    """
    documento = request.GET.get('documento', '').strip()
    
    # Remove pontuação
    documento_limpo = re.sub(r'\D', '', documento)
    
    if not documento_limpo:
        return JsonResponse({
            'found': False, 
            'id': None, 
            'nome': '', 
            'tipo_pessoa': '',
            'telefone': '',
            'email': '',
            'endereco': ''
        })
    
    # Busca por CPF ou CNPJ
    cliente = Cliente.objects.filter(
        Q(cpf=documento_limpo) | Q(cnpj=documento_limpo)
    ).first()
    
    if cliente:
        return JsonResponse({
            'found': True,
            'id': cliente.id,
            'nome': cliente.nome,
            'tipo_pessoa': cliente.tipo_pessoa,
            'telefone': cliente.telefone or '',
            'email': cliente.email or '',
            'endereco': cliente.endereco or '',
        })
    
    return JsonResponse({
        'found': False, 
        'id': None, 
        'nome': '', 
        'tipo_pessoa': '',
        'telefone': '',
        'email': '',
        'endereco': ''
    })


# ========== PROTOCOLOS - CERTIDÃO ==========

def _limpar_documento(valor):
    """Remove pontuação de documento, mantendo apenas números."""
    if valor:
        return re.sub(r'\D', '', valor)
    return None


def _processar_pessoas_do_post(request, prefixo, apenas_cpf=False):
    """
    Processa os dados de clientes/advogados enviados via POST.
    Retorna lista de objetos Cliente (criados ou atualizados).
    
    Usa update_or_create para manter cadastros atualizados.
    
    Parâmetros:
    - prefixo: 'cliente' ou 'advogado'
    - apenas_cpf: Se True, força tipo FISICA (para advogados)
    
    Espera campos no formato:
    - {prefixo}_documento[]
    - {prefixo}_nome[]
    - {prefixo}_telefone[]
    - {prefixo}_email[]
    - {prefixo}_endereco[]
    - {prefixo}_id[] (opcional, para clientes já existentes)
    """
    documentos = request.POST.getlist(f'{prefixo}_documento[]')
    nomes = request.POST.getlist(f'{prefixo}_nome[]')
    telefones = request.POST.getlist(f'{prefixo}_telefone[]')
    emails = request.POST.getlist(f'{prefixo}_email[]')
    enderecos = request.POST.getlist(f'{prefixo}_endereco[]')
    ids = request.POST.getlist(f'{prefixo}_id[]')
    
    pessoas = []
    
    for i, doc in enumerate(documentos):
        doc_limpo = _limpar_documento(doc)
        nome = nomes[i].strip() if i < len(nomes) else ''
        telefone = telefones[i].strip() if i < len(telefones) else ''
        email = emails[i].strip() if i < len(emails) else ''
        endereco = enderecos[i].strip() if i < len(enderecos) else ''
        cliente_id = ids[i] if i < len(ids) else ''
        
        if not doc_limpo and not nome:
            continue  # Linha vazia
        
        # Determina tipo de pessoa pelo tamanho do documento
        # Se apenas_cpf=True (advogado), força pessoa física
        if apenas_cpf or len(doc_limpo) == 11:
            tipo_pessoa = Cliente.TipoPessoa.FISICA
            cpf = doc_limpo[:11] if doc_limpo else None  # Garante máximo 11 dígitos
            cnpj = None
        elif len(doc_limpo) == 14:
            tipo_pessoa = Cliente.TipoPessoa.JURIDICA
            cpf = None
            cnpj = doc_limpo
        else:
            # Documento inválido, tenta como CPF
            tipo_pessoa = Cliente.TipoPessoa.FISICA
            cpf = doc_limpo if doc_limpo else None
            cnpj = None
        
        if not nome:
            continue  # Sem nome, não cria
        
        # Dados para criar/atualizar
        dados_cliente = {
            'nome': nome,
            'tipo_pessoa': tipo_pessoa,
        }
        
        # Só atualiza campos opcionais se preenchidos
        if telefone:
            dados_cliente['telefone'] = telefone
        if email:
            dados_cliente['email'] = email
        if endereco:
            dados_cliente['endereco'] = endereco
        
        # Usa update_or_create para criar ou atualizar o cliente
        if cpf:
            cliente, created = Cliente.objects.update_or_create(
                cpf=cpf,
                defaults=dados_cliente
            )
        elif cnpj:
            cliente, created = Cliente.objects.update_or_create(
                cnpj=cnpj,
                defaults=dados_cliente
            )
        else:
            # Sem documento válido, cria novo apenas pelo nome (caso especial)
            cliente = Cliente.objects.create(**dados_cliente)
        
        pessoas.append(cliente)
    
    return pessoas


def _processar_lista_documentos(request):
    """Processa a lista de documentos enviada via POST."""
    documentos = request.POST.getlist('documento_item[]')
    return [doc.strip() for doc in documentos if doc.strip()]


@login_required
@transaction.atomic
def protocolo_certidao_create(request):
    """
    Cria um novo Protocolo do tipo Certidão.
    Processa clientes, advogados e documentos manualmente.
    """
    if request.method == 'POST':
        form = ProtocoloCertidaoForm(request.POST)
        
        if form.is_valid():
            # Salva o protocolo (numero_protocolo é gerado automaticamente no model)
            protocolo = form.save(commit=False)
            protocolo.tipo = Protocolo.TipoProtocolo.CERTIDAO
            protocolo.criado_por = request.user
            protocolo.responsavel = request.user
            
            # Processa lista de documentos
            protocolo.lista_documentos = _processar_lista_documentos(request)
            
            protocolo.save()  # Número gerado automaticamente aqui
            
            # Processa clientes (solicitantes) - permite CPF ou CNPJ
            clientes = _processar_pessoas_do_post(request, 'cliente', apenas_cpf=False)
            if clientes:
                protocolo.clientes.set(clientes)
            
            # Processa advogados (se houver) - apenas CPF (pessoa física)
            tem_advogado = request.POST.get('tem_advogado') == 'on'
            if tem_advogado:
                advogados = _processar_pessoas_do_post(request, 'advogado', apenas_cpf=True)
                if advogados:
                    protocolo.advogados.set(advogados)
            
            messages.success(request, f'Protocolo {protocolo.numero_protocolo} criado com sucesso!')
            return redirect('protocolo_certidao_update', pk=protocolo.pk)
        else:
            # Form inválido, recupera dados para repopular
            pass
    else:
        form = ProtocoloCertidaoForm()
    
    context = {
        'form': form,
        'title': 'Novo Protocolo de Certidão',
        'button_text': 'Salvar Protocolo',
        'is_edit': False,
        'clientes_data': [],
        'advogados_data': [],
        'documentos_data': [],
        'has_advogados': False,
    }
    return render(request, 'core/protocolo_certidao_form.html', context)


@login_required
@transaction.atomic
def protocolo_certidao_update(request, pk):
    """
    Edita um protocolo do tipo Certidão existente.
    """
    protocolo = get_object_or_404(
        Protocolo,
        pk=pk,
        tipo=Protocolo.TipoProtocolo.CERTIDAO
    )
    
    if request.method == 'POST':
        form = ProtocoloCertidaoForm(request.POST, instance=protocolo)
        
        if form.is_valid():
            # Salva o protocolo
            protocolo = form.save(commit=False)
            protocolo.tipo = Protocolo.TipoProtocolo.CERTIDAO
            
            # Processa lista de documentos
            protocolo.lista_documentos = _processar_lista_documentos(request)
            
            protocolo.save()
            
            # Processa clientes (solicitantes) - permite CPF ou CNPJ
            clientes = _processar_pessoas_do_post(request, 'cliente', apenas_cpf=False)
            protocolo.clientes.set(clientes)
            
            # Processa advogados (se houver) - apenas CPF (pessoa física)
            tem_advogado = request.POST.get('tem_advogado') == 'on'
            if tem_advogado:
                advogados = _processar_pessoas_do_post(request, 'advogado', apenas_cpf=True)
                protocolo.advogados.set(advogados)
            else:
                protocolo.advogados.clear()
            
            messages.success(request, f'Protocolo {protocolo.numero_protocolo} atualizado com sucesso!')
            return redirect('protocolo_certidao_update', pk=protocolo.pk)
    else:
        form = ProtocoloCertidaoForm(instance=protocolo)
    
    # Prepara dados para o template (incluindo dados completos para edição)
    clientes_data = [
        {
            'id': c.id, 
            'documento': c.cpf or c.cnpj or '', 
            'nome': c.nome,
            'telefone': c.telefone or '',
            'email': c.email or '',
            'endereco': c.endereco or '',
        }
        for c in protocolo.clientes.all()
    ]
    advogados_data = [
        {
            'id': a.id, 
            'documento': a.cpf or a.cnpj or '', 
            'nome': a.nome,
            'telefone': a.telefone or '',
            'email': a.email or '',
            'endereco': a.endereco or '',
        }
        for a in protocolo.advogados.all()
    ]
    documentos_data = protocolo.lista_documentos or []
    
    context = {
        'form': form,
        'title': f'Editar Certidão #{protocolo.numero_protocolo}',
        'button_text': 'Atualizar Protocolo',
        'is_edit': True,
        'protocolo': protocolo,
        'clientes_data': json.dumps(clientes_data),
        'advogados_data': json.dumps(advogados_data),
        'documentos_data': json.dumps(documentos_data),
        'has_advogados': protocolo.advogados.exists(),
    }
    return render(request, 'core/protocolo_certidao_form.html', context)
