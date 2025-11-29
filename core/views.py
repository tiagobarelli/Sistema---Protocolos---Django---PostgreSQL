from django.shortcuts import render, redirect
from django.contrib.auth import login, get_user_model
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import SetupMasterForm

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
            # Redireciona para a home/dashboard (que criaremos depois)
            return redirect('/') 
    else:
        form = SetupMasterForm()

    return render(request, 'core/setup.html', {'form': form})

@login_required
def dashboard(request):
    return render(request, 'core/dashboard.html')    